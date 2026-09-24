import logging

from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import SavedMatch, NotificationPreference, ContactMessage
from apps.news.models import ArticleBookmark, ArticleComment, NewsArticle
from apps.videos.models import CricketVideo, VideoBookmark
from apps.photos.models import PhotoAlbum, PhotoItem
from apps.matches.models import Ground, Match, Tournament
from apps.teams.models import Team
from apps.players.models import Player
from apps.accounts.models import CustomUser
from .forms import (
    LocalGroundForm, LocalMatchForm, LocalPlayerForm, LocalTeamForm,
    LocalTournamentForm, ManagedUserForm, ScorerAssignmentForm,
    VenueForm, SimplePhotoForm, SimpleNewsForm, SimpleVideoUploadForm,
    ContactForm,
)

logger = logging.getLogger(__name__)

User = get_user_model()

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Core Metrics
        context['total_users'] = User.objects.count()
        context['total_matches'] = Match.objects.count()
        context['live_matches_count'] = Match.objects.filter(status=Match.Status.LIVE).count()
        context['completed_matches_count'] = Match.objects.filter(status=Match.Status.COMPLETED).count()
        context['upcoming_matches_count'] = Match.objects.filter(status=Match.Status.UPCOMING).count()
        context['total_teams'] = Team.objects.count()
        context['total_players'] = Player.objects.count()
        context['total_news'] = NewsArticle.objects.count()
        context['total_videos'] = CricketVideo.objects.count()
        context['total_albums'] = PhotoAlbum.objects.count()

        # Contact inbox metrics
        context['unread_messages_count'] = ContactMessage.objects.filter(
            is_read=False, is_deleted=False
        ).count()

        # Pending player registration requests badge
        from apps.players.models import PlayerRegistrationRequest
        context['pending_requests_count'] = PlayerRegistrationRequest.objects.filter(
            status=PlayerRegistrationRequest.Status.PENDING
        ).count()

        # Format Breakdown for Chart.js
        t20_count = Match.objects.filter(match_type=Match.MatchType.T20).count()
        odi_count = Match.objects.filter(match_type=Match.MatchType.ODI).count()
        test_count = Match.objects.filter(match_type=Match.MatchType.TEST).count()
        context['match_format_counts'] = {
            'T20': t20_count,
            'ODI': odi_count,
            'TEST': test_count
        }

        # Recent Activity & Latest Users
        context['latest_users'] = User.objects.order_by('-created_at')[:6]
        context['recent_comments'] = ArticleComment.objects.select_related('user', 'article').order_by('-created_at')[:6]
        context['recent_matches'] = Match.objects.select_related('team1', 'team2', 'venue').order_by('-created_at')[:5]
        context['active_scorers'] = User.objects.filter(
            role=CustomUser.Role.SCORER, is_deleted=False,
        ).order_by('email')
        context['scorer_assignment_form'] = ScorerAssignmentForm()

        return context

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['saved_matches_count'] = user.saved_matches.count()
        context['saved_news_count'] = user.news_bookmarks.count()
        context['saved_videos_count'] = user.video_bookmarks.count()
        context['comments_count'] = user.article_comments.count()

        # Recent saves
        context['recent_saved_matches'] = user.saved_matches.select_related('match__team1', 'match__team2', 'match__venue')[:3]
        context['recent_saved_news'] = user.news_bookmarks.select_related('article__category')[:3]
        context['recent_saved_videos'] = user.video_bookmarks.select_related('video__category')[:3]

        # Live matches happening now
        context['ongoing_matches'] = Match.objects.filter(status=Match.Status.LIVE).select_related('team1', 'team2')[:4]

        # Latest videos for the Home page video section
        context['latest_uploaded_videos'] = CricketVideo.objects.filter(is_active=True).order_by('-created_at')[:6]
        return context


class RoleDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        allowed = request.user.is_superuser
        if self.required_role != CustomUser.Role.SUPER_ADMIN:
            allowed = allowed or request.user.role == self.required_role
        if self.required_role and not allowed:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dashboard_role'] = self.request.user.get_role_display()
        return context


class SuperAdminDashboardView(RoleDashboardView):
    required_role = CustomUser.Role.SUPER_ADMIN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['managed_admins_count'] = User.objects.filter(
            role=CustomUser.Role.ADMIN, is_deleted=False,
        ).count()
        context['managed_scorers_count'] = User.objects.filter(
            role=CustomUser.Role.SCORER, is_deleted=False,
        ).count()
        return context


class ScorerDashboardView(RoleDashboardView):
    required_role = CustomUser.Role.SCORER
    template_name = 'dashboard/scorer_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assigned_matches'] = (
            Match.objects.filter(assigned_scorers=self.request.user)
            .select_related('team1', 'team2', 'tournament', 'ground__venue')
            .order_by('start_datetime')
        )
        return context


class ManagedUsersView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'dashboard/managed_users.html'

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role == CustomUser.Role.ADMIN

    def get_role(self):
        if self.request.user.is_superuser and self.request.GET.get('role') == CustomUser.Role.ADMIN:
            return CustomUser.Role.ADMIN
        return CustomUser.Role.SCORER

    def get(self, request):
        role = self.get_role()
        users = User.objects.filter(role=role, is_deleted=False).order_by('email')
        selected = users.filter(pk=request.GET.get('edit')).first()
        return render(request, self.template_name, {
            'role': role,
            'users': users,
            'form': ManagedUserForm(instance=selected, role=role),
            'is_editing': bool(selected),
        })

    def post(self, request):
        action = request.POST.get('action', 'save')
        role = request.POST.get('role', self.get_role())
        if role == CustomUser.Role.ADMIN and not request.user.is_superuser:
            raise PermissionDenied
        if role not in (CustomUser.Role.ADMIN, CustomUser.Role.SCORER):
            raise PermissionDenied

        user = User.objects.filter(pk=request.POST.get('user_id'), role=role).first()
        if action == 'delete':
            if not user:
                raise PermissionDenied
            user.soft_delete()
            return redirect(f'{request.path}?role={role}')
        if action == 'reset_password':
            if not user:
                raise PermissionDenied
            password = request.POST.get('password', '')
            try:
                validate_password(password, user)
            except ValidationError as exc:
                return JsonResponse({'success': False, 'errors': exc.messages}, status=400)
            user.set_password(password)
            user.save(update_fields=['password', 'updated_at'])
            return redirect(f'{request.path}?role={role}')
        if action == 'toggle':
            if not user:
                raise PermissionDenied
            user.is_active = not user.is_active
            user.save(update_fields=['is_active', 'updated_at'])
            return redirect(f'{request.path}?role={role}')

        form = ManagedUserForm(request.POST, instance=user, role=role)
        if form.is_valid():
            form.save()
            return redirect(f'{request.path}?role={role}')
        users = User.objects.filter(role=role, is_deleted=False).order_by('email')
        return render(request, self.template_name, {
            'role': role, 'users': users, 'form': form,
            'is_editing': bool(user),
        })


class AssignScorersView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role == CustomUser.Role.ADMIN

    def post(self, request):
        form = ScorerAssignmentForm(request.POST)
        if not form.is_valid():
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        match = form.cleaned_data['match']
        
        # Ensure match has a slug before redirecting
        if not match.slug:
            match.save()  # This will generate the slug if it doesn't exist
        
        match.assigned_scorers.set(form.cleaned_data['scorers'])
        return JsonResponse({
            'success': True, 
            'message': 'Scorer assigned successfully.',
            'match_slug': match.slug
        })


class LocalManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'dashboard/local_management.html'
    forms = {
        'match': (Match, LocalMatchForm, 'Manage Local Matches'),
        'team': (Team, LocalTeamForm, 'Manage Teams'),
        'player': (Player, LocalPlayerForm, 'Manage Players'),
        'tournament': (Tournament, LocalTournamentForm, 'Manage Tournaments'),
        'ground': (Ground, LocalGroundForm, 'Manage Grounds'),
    }

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == CustomUser.Role.ADMIN

    def get_config(self):
        config = self.forms.get(self.kwargs.get('entity'))
        if not config:
            raise PermissionDenied
        return config

    @staticmethod
    def _identifier(value):
        """Return a usable primary-key value, never an empty string."""
        value = str(value or '').strip()
        return value or None

    @staticmethod
    def _wants_venue_create(post_data):
        """Only treat explicit enable values as venue creation; '0' is false."""
        return str(post_data.get('create_venue') or '').strip().lower() in {
            '1', 'true', 'on', 'yes',
        }

    @staticmethod
    def _normalise_relation_values(form_class, data):
        """Let ModelForms receive None/empty lists for blank UUID relations."""
        normalized = data.copy()
        for name, field in form_class.base_fields.items():
            if isinstance(field, forms.ModelMultipleChoiceField):
                if not any(str(value).strip() for value in normalized.getlist(name)):
                    normalized.setlist(name, [])
            elif isinstance(field, forms.ModelChoiceField):
                raw = normalized.get(name)
                if raw is None or not str(raw).strip() or str(raw).strip().lower() in {
                    'none', 'null', 'undefined',
                }:
                    normalized[name] = ''
        return normalized

    def _venue_form(self, request=None, bind=False):
        kwargs = {'prefix': 'venue'}
        if bind and request is not None:
            return VenueForm(request.POST, request.FILES, **kwargs)
        return VenueForm(**kwargs)

    def _page_context(self, request, entity, model, form_class, title, form, record, lookup_error, venue_form):
        return {
            'entity': entity,
            'title': title,
            'form': form,
            'records': model.objects.all().order_by('-pk')[:100],
            'model_name': model._meta.verbose_name,
            'editing_id': record.pk if record else '',
            'lookup_error': lookup_error,
            'venue_form': venue_form,
            'has_venues': form.fields['venue'].queryset.exists() if entity == 'ground' else False,
        }

    def _redirect_saved(self, request, entity, saved):
        messages.success(request, f'{saved} saved successfully.')
        logger.info('local_management saved entity=%s pk=%s', entity, saved.pk)
        return redirect(
            f"{reverse('dashboard:local_management', kwargs={'entity': entity})}?edit={saved.pk}"
        )

    def _apply_save_exception(self, form, exc):
        message = (
            'This record could not be saved because one of its values '
            'conflicts with an existing record. Review the highlighted fields.'
        )
        form.add_error(None, message)
        if isinstance(exc, ValidationError):
            error_dict = getattr(exc, 'error_dict', None) or getattr(exc, 'message_dict', None)
            if error_dict:
                for field, errors in error_dict.items():
                    form.add_error(field if field in form.fields else None, errors)
            else:
                form.add_error(None, getattr(exc, 'messages', [str(exc)]))

    def _find_record(self, model, value):
        identifier = self._identifier(value)
        if identifier is None:
            return None, None
        try:
            return model.objects.filter(pk=identifier).first(), None
        except (ValidationError, ValueError, TypeError):
            return None, 'The selected record identifier is invalid.'

    def get(self, request, entity):
        model, form_class, title = self.get_config()
        selected, lookup_error = self._find_record(model, request.GET.get('edit'))
        form = form_class(instance=selected)
        venue_form = self._venue_form() if entity == 'ground' else None
        return render(
            request,
            self.template_name,
            self._page_context(
                request, entity, model, form_class, title, form,
                selected, lookup_error, venue_form,
            ),
        )

    def post(self, request, entity):
        model, form_class, title = self.get_config()
        if entity == 'player' and request.POST.get('action') == 'delete':
            record, lookup_error = self._find_record(model, request.POST.get('record_id'))
            if lookup_error:
                messages.error(request, lookup_error)
            elif record is None:
                messages.error(request, 'Player not found.')
            else:
                player_name = str(record)
                record.delete()
                messages.success(request, f'Player "{player_name}" deleted successfully.')
            return redirect('dashboard:local_management', entity='player')

        record, lookup_error = self._find_record(model, request.POST.get('record_id'))
        data = self._normalise_relation_values(form_class, request.POST)
        creating_venue = entity == 'ground' and self._wants_venue_create(request.POST)
        logger.info(
            'local_management POST entity=%s creating_venue=%s record_id=%s',
            entity, creating_venue, request.POST.get('record_id'),
        )

        venue_form = None
        if entity == 'ground':
            venue_form = self._venue_form(request, bind=creating_venue)

        form_kwargs = {'creating_venue': creating_venue} if entity == 'ground' else {}
        venue_valid = True
        if creating_venue:
            venue_valid = venue_form.is_valid()
            logger.info('venue form valid=%s errors=%s', venue_valid, venue_form.errors.as_json())
            if venue_valid:
                try:
                    with transaction.atomic():
                        venue = venue_form.save()
                        data['venue'] = str(venue.pk)
                        form = form_class(data, request.FILES, instance=record, **form_kwargs)
                        if form.is_valid() and not lookup_error:
                            saved = form.save()
                            return self._redirect_saved(request, entity, saved)
                        logger.info('ground form invalid after venue create: %s', form.errors.as_json())
                        form.add_error(
                            None,
                            'Review the ground fields. The new venue was not kept because the ground could not be saved.',
                        )
                        transaction.set_rollback(True)
                except (ValidationError, IntegrityError) as exc:
                    logger.exception('ground+venue save failed')
                    form = form_class(data, request.FILES, instance=record, **form_kwargs)
                    self._apply_save_exception(form, exc)
            else:
                form = form_class(data, request.FILES, instance=record, **form_kwargs)
                form.add_error(None, 'Create the venue first. Review the venue fields below.')
        else:
            form = form_class(data, request.FILES, instance=record, **form_kwargs)

        if lookup_error:
            form.add_error(None, lookup_error)

        if form.is_valid() and not lookup_error and venue_valid:
            try:
                with transaction.atomic():
                    saved = form.save()
            except (ValidationError, IntegrityError) as exc:
                logger.exception('local_management save failed entity=%s', entity)
                self._apply_save_exception(form, exc)
            else:
                return self._redirect_saved(request, entity, saved)
        else:
            logger.info(
                'local_management not saved entity=%s form_valid=%s venue_valid=%s errors=%s',
                entity, form.is_valid(), venue_valid, form.errors.as_json(),
            )
            if form.errors:
                messages.error(request, 'Could not save this record. Review the highlighted fields.')

        if entity == 'ground' and venue_form is None:
            venue_form = self._venue_form()
        return render(
            request,
            self.template_name,
            self._page_context(
                request, entity, model, form_class, title, form,
                record, lookup_error, venue_form,
            ),
        )


class SavedItemsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/saved_items.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tab = self.request.GET.get('tab', 'matches')

        context['active_tab'] = tab
        context['saved_matches'] = user.saved_matches.select_related('match__team1', 'match__team2', 'match__venue')
        context['saved_news'] = user.news_bookmarks.select_related('article__category')
        context['saved_videos'] = user.video_bookmarks.select_related('video__category')
        return context


class NotificationSettingsView(LoginRequiredMixin, View):
    template_name = 'dashboard/notifications.html'

    def get(self, request):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
        return render(request, self.template_name, {'pref': pref})

    def post(self, request):
        pref, _ = NotificationPreference.objects.get_or_create(user=request.user)

        pref.email_match_start = 'email_match_start' in request.POST
        pref.email_match_result = 'email_match_result' in request.POST
        pref.email_breaking_news = 'email_breaking_news' in request.POST
        pref.browser_live_score = 'browser_live_score' in request.POST
        pref.browser_wicket_alerts = 'browser_wicket_alerts' in request.POST
        pref.sound_effects = 'sound_effects' in request.POST

        pref.save()
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('dashboard:notifications')


class UserCommentsListView(LoginRequiredMixin, ListView):
    model = ArticleComment
    template_name = 'dashboard/my_comments.html'
    context_object_name = 'comments'
    paginate_by = 15

    def get_queryset(self):
        return ArticleComment.objects.filter(user=self.request.user).select_related('article')


class ToggleSaveMatchView(LoginRequiredMixin, View):
    def post(self, request, match_id):
        match = get_object_or_404(Match, id=match_id)
        saved, created = SavedMatch.objects.get_or_create(user=request.user, match=match)

        if not created:
            saved.delete()
            is_saved = False
            message = 'Match removed from saved list'
        else:
            is_saved = True
            message = 'Match added to your saved watchlist'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'is_saved': is_saved, 'message': message})
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer) if referer else redirect('matches:match_detail', slug=match.slug)


class WebsiteSettingsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'dashboard/website_settings.html'

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get(self, request):
        from .models import SiteSetting
        setting = SiteSetting.get_settings()
        return render(request, self.template_name, {'setting': setting})

    def post(self, request):
        from .models import SiteSetting
        setting = SiteSetting.get_settings()

        # Only the simplified, safe-to-edit fields are handled here. All other
        # SiteSetting fields (branding, colors, banner, logo, footer text, ...)
        # are intentionally left untouched so existing data is preserved.
        setting.about_us = request.POST.get('about_us', setting.about_us).strip()
        setting.contact_email = request.POST.get('contact_email', setting.contact_email).strip()
        setting.contact_phone = request.POST.get('contact_phone', setting.contact_phone).strip()
        setting.address = request.POST.get('address', setting.address).strip()
        setting.facebook_url = request.POST.get('facebook_url', setting.facebook_url).strip()
        setting.twitter_url = request.POST.get('twitter_url', setting.twitter_url).strip()
        setting.instagram_url = request.POST.get('instagram_url', setting.instagram_url).strip()
        setting.youtube_url = request.POST.get('youtube_url', setting.youtube_url).strip()

        setting.save()
        messages.success(request, 'Website settings saved!')
        return redirect('dashboard:website_settings')


class PhotoManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Dashboard view for Photo management - CRUD operations"""
    template_name = 'dashboard/photo_management.html'

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get(self, request):
        photos = PhotoItem.objects.select_related('album').order_by('-created_at')
        form = SimplePhotoForm()
        editing_photo = None
        return render(request, self.template_name, {
            'photos': photos,
            'form': form,
            'editing_photo': editing_photo
        })

    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'create':
            form = SimplePhotoForm(request.POST, request.FILES)
            if form.is_valid():
                # Create a default album if needed
                from apps.photos.models import PhotoAlbum
                default_album, _ = PhotoAlbum.objects.get_or_create(
                    title='General Photos',
                    defaults={'slug': 'general-photos', 'category': 'stadium'}
                )
                photo = form.save(commit=False)
                photo.album = default_album
                photo.save()
                messages.success(request, 'Photo uploaded successfully!')
                return redirect('dashboard:photo_management')
            else:
                photos = PhotoItem.objects.select_related('album').order_by('-created_at')
                return render(request, self.template_name, {
                    'photos': photos,
                    'form': form,
                    'editing_photo': None
                })
        
        elif action == 'edit':
            photo_id = request.POST.get('photo_id')
            photo = get_object_or_404(PhotoItem, id=photo_id)
            form = SimplePhotoForm(request.POST, request.FILES, instance=photo)
            if form.is_valid():
                form.save()
                messages.success(request, 'Photo updated successfully!')
                return redirect('dashboard:photo_management')
            else:
                photos = PhotoItem.objects.select_related('album').order_by('-created_at')
                return render(request, self.template_name, {
                    'photos': photos,
                    'form': form,
                    'editing_photo': photo
                })
        
        elif action == 'delete':
            photo_id = request.POST.get('photo_id')
            photo = get_object_or_404(PhotoItem, id=photo_id)
            photo.delete()
            messages.success(request, 'Photo deleted successfully!')
            return redirect('dashboard:photo_management')
        
        return redirect('dashboard:photo_management')


class NewsManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Dashboard view for News management - CRUD operations"""
    template_name = 'dashboard/news_management.html'

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get(self, request):
        news_articles = NewsArticle.objects.select_related('category', 'author').order_by('-published_at')
        form = SimpleNewsForm()
        return render(request, self.template_name, {
            'news_articles': news_articles,
            'form': form,
            'editing_news': None
        })

    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'create':
            form = SimpleNewsForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, 'News article published successfully!')
                return redirect('dashboard:news_management')
            else:
                news_articles = NewsArticle.objects.select_related('category', 'author').order_by('-published_at')
                return render(request, self.template_name, {
                    'news_articles': news_articles,
                    'form': form,
                    'editing_news': None
                })
        
        elif action == 'edit':
            news_id = request.POST.get('news_id')
            news = get_object_or_404(NewsArticle, id=news_id)
            form = SimpleNewsForm(request.POST, request.FILES, instance=news)
            if form.is_valid():
                form.save()
                messages.success(request, 'News article updated successfully!')
                return redirect('dashboard:news_management')
            else:
                news_articles = NewsArticle.objects.select_related('category', 'author').order_by('-published_at')
                return render(request, self.template_name, {
                    'news_articles': news_articles,
                    'form': form,
                    'editing_news': news
                })
        
        elif action == 'delete':
            news_id = request.POST.get('news_id')
            news = get_object_or_404(NewsArticle, id=news_id)
            news.delete()
            messages.success(request, 'News article deleted successfully!')
            return redirect('dashboard:news_management')
        
        return redirect('dashboard:news_management')


class VideoManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Dashboard view for Uploaded Video management - CRUD operations"""
    template_name = 'dashboard/video_management.html'

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    @staticmethod
    def _find_video(raw_id):
        """Return the CricketVideo for an id taken from the request, or None."""
        try:
            return CricketVideo.objects.filter(id=raw_id).first()
        except (ValidationError, ValueError, TypeError):
            return None

    def get(self, request):
        return self._render(request, SimpleVideoUploadForm())

    def post(self, request):
        action = request.POST.get('action')

        if action == 'delete':
            video = self._find_video(request.POST.get('video_id'))
            if video is None:
                messages.error(request, 'That video could not be found.')
                return redirect('dashboard:video_management')
            video.delete()
            messages.success(request, 'Video deleted successfully!')
            return redirect('dashboard:video_management')

        editing_video = None
        if action == 'edit':
            editing_video = self._find_video(request.POST.get('video_id'))
            if editing_video is None:
                messages.error(request, 'That video could not be found.')
                return redirect('dashboard:video_management')

        form = SimpleVideoUploadForm(request.POST, request.FILES, instance=editing_video)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Video updated successfully!' if editing_video else 'Video uploaded successfully!',
            )
            return redirect('dashboard:video_management')

        messages.error(request, 'Could not save this video. Review the highlighted fields.')
        return self._render(request, form, editing_video)

    def _render(self, request, form, editing_video=None):
        return render(request, self.template_name, {
            'videos': CricketVideo.objects.filter(is_active=True).order_by('-created_at'),
            'form': form,
            'editing_video': editing_video,
        })


class ContactView(View):
    """Public Contact Us page. Saves the submitted message to the admin inbox.

    No login is required and no email is sent — the message is only stored.
    """
    template_name = 'pages/contact.html'

    def get(self, request):
        return render(request, self.template_name, {'form': ContactForm()})

    def post(self, request):
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Thank you! Your message has been sent to our desk.',
            )
            return redirect('contact')
        return render(request, self.template_name, {'form': form})


class MessagesListView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Admin inbox listing every contact message (search, filter, paginate)."""
    template_name = 'dashboard/messages_list.html'
    paginate_by = 20

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get(self, request):
        from django.core.paginator import Paginator
        from django.db.models import Q

        qs = ContactMessage.objects.filter(is_deleted=False).order_by('-created_at')

        query         = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', 'all').strip()

        if status_filter in ('read', 'unread'):
            qs = qs.filter(is_read=(status_filter == 'read'))

        if query:
            qs = qs.filter(
                Q(full_name__icontains=query)
                | Q(email__icontains=query)
                | Q(subject__icontains=query)
            )

        paginator = Paginator(qs, self.paginate_by)
        page_obj  = paginator.get_page(request.GET.get('page', 1))

        unread_messages_count = ContactMessage.objects.filter(
            is_read=False, is_deleted=False
        ).count()

        return render(request, self.template_name, {
            'page_obj':              page_obj,
            'query':                 query,
            'status_filter':         status_filter,
            'unread_messages_count': unread_messages_count,
        })


class MessageDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Shows a single contact message and marks it read on first open."""
    template_name = 'dashboard/message_detail.html'

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get(self, request, pk):
        msg = get_object_or_404(ContactMessage, pk=pk, is_deleted=False)
        if not msg.is_read:
            msg.is_read = True
            msg.save(update_fields=['is_read'])
        unread_messages_count = ContactMessage.objects.filter(
            is_read=False, is_deleted=False
        ).count()
        return render(request, self.template_name, {
            'msg':                   msg,
            'unread_messages_count': unread_messages_count,
        })


class MessageActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """POST-only: mark a contact message read/unread or (soft) delete it."""

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def post(self, request, pk):
        msg    = get_object_or_404(ContactMessage, pk=pk, is_deleted=False)
        action = request.POST.get('action')

        if action == 'mark_read':
            msg.is_read = True
            msg.save(update_fields=['is_read'])
            messages.success(request, 'Message marked as read.')
        elif action == 'mark_unread':
            msg.is_read = False
            msg.save(update_fields=['is_read'])
            messages.success(request, 'Message marked as unread.')
        elif action == 'delete':
            msg.is_deleted = True
            msg.save(update_fields=['is_deleted'])
            messages.success(request, 'Message deleted.')
            return redirect('dashboard:messages_list')

        return redirect('dashboard:message_detail', pk=pk)


class PlayerRequestsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Admin list of all PlayerRegistrationRequest records.
    Supports search, status filter, country filter and pagination.
    """
    template_name = 'dashboard/player_requests.html'
    paginate_by = 20

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get(self, request):
        from apps.players.models import PlayerRegistrationRequest
        from django.core.paginator import Paginator

        qs = PlayerRegistrationRequest.objects.select_related('team').order_by('-submitted_at')

        status_filter  = request.GET.get('status', 'pending').strip()
        country_filter = request.GET.get('country', '').strip()
        query          = request.GET.get('q', '').strip()

        if status_filter in ('pending', 'approved', 'rejected'):
            qs = qs.filter(status=status_filter)

        if country_filter:
            qs = qs.filter(country__icontains=country_filter)

        if query:
            qs = qs.filter(
                Q(full_name__icontains=query)
                | Q(mobile_number__icontains=query)
                | Q(country__icontains=query)
            )

        paginator  = Paginator(qs, self.paginate_by)
        page_obj   = paginator.get_page(request.GET.get('page', 1))

        countries = (
            PlayerRegistrationRequest.objects
            .exclude(country='')
            .values_list('country', flat=True)
            .distinct()
            .order_by('country')
        )

        pending_count = PlayerRegistrationRequest.objects.filter(
            status=PlayerRegistrationRequest.Status.PENDING
        ).count()

        return render(request, self.template_name, {
            'page_obj':       page_obj,
            'status_filter':  status_filter,
            'country_filter': country_filter,
            'query':          query,
            'countries':      countries,
            'pending_count':  pending_count,
            'status_choices': PlayerRegistrationRequest.Status.choices,
        })


class PlayerRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Shows every field of a single PlayerRegistrationRequest.
    Provides Accept and Reject buttons.
    """
    template_name = 'dashboard/player_request_detail.html'

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def get(self, request, pk):
        from apps.players.models import PlayerRegistrationRequest
        from django.shortcuts import get_object_or_404
        req = get_object_or_404(
            PlayerRegistrationRequest.objects.select_related('team', 'approved_player'),
            pk=pk,
        )
        return render(request, self.template_name, {'req': req})


class PlayerRequestActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    POST-only.  Accepts or rejects a PlayerRegistrationRequest.

    Accept:
        - Creates a new Player from the request data.
        - Sets request.status = approved and links request.approved_player.
        - Player is immediately active and approved, visible everywhere.

    Reject:
        - Sets request.status = rejected + records rejection_date.
        - No Player is ever created.
        - Admin can reopen (approve) later; the form data is preserved.
    """

    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'role', '') == CustomUser.Role.ADMIN

    def post(self, request, pk):
        from apps.players.models import Player, PlayerRegistrationRequest
        from django.shortcuts import get_object_or_404
        from django.utils import timezone

        req    = get_object_or_404(PlayerRegistrationRequest, pk=pk)
        action = request.POST.get('action')

        if action == 'approve':
            # Guard: do not create a duplicate Player if already approved
            if req.status == PlayerRegistrationRequest.Status.APPROVED and req.approved_player:
                messages.info(request, f'{req.full_name} is already approved.')
                return redirect('dashboard:player_request_detail', pk=pk)

            # Build and save the Player record
            player = Player(
                name          = req.full_name,
                mobile_number = req.mobile_number,
                email_address = req.email_address,
                full_address  = req.full_address,
                born_date     = req.date_of_birth,
                jersey_number = req.jersey_number,
                role          = req.playing_role,
                batting_style = req.batting_style,
                bowling_style = req.bowling_style,
                primary_team  = req.team,
                country       = req.country,
                biography     = req.short_bio,
                image         = req.photo,
                # Immediately live
                is_active            = True,
                registration_status  = Player.RegistrationStatus.APPROVED,
            )
            player.save()

            # Link request → player and mark approved
            req.approved_player = player
            req.status          = PlayerRegistrationRequest.Status.APPROVED
            req.rejection_date  = None
            req.save(update_fields=['approved_player', 'status', 'rejection_date', 'updated_at'])

            messages.success(
                request,
                f'✅ {req.full_name} has been approved and is now visible on the website.',
            )
            return redirect('dashboard:player_requests')

        elif action == 'reject':
            req.status         = PlayerRegistrationRequest.Status.REJECTED
            req.rejection_date = timezone.now()
            req.save(update_fields=['status', 'rejection_date', 'updated_at'])
            messages.warning(
                request,
                f'❌ {req.full_name} has been rejected and will not appear publicly.',
            )
            return redirect('dashboard:player_requests')

        messages.error(request, 'Invalid action.')
        return redirect('dashboard:player_request_detail', pk=pk)
