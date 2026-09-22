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
from .models import SavedMatch, NotificationPreference
from apps.news.models import ArticleBookmark, ArticleComment, NewsArticle
from apps.videos.models import CricketVideo, VideoBookmark
from apps.photos.models import PhotoAlbum
from apps.matches.models import Ground, Match, Tournament
from apps.teams.models import Team
from apps.players.models import Player
from apps.accounts.models import CustomUser
from .forms import (
    LocalGroundForm, LocalMatchForm, LocalPlayerForm, LocalTeamForm,
    LocalTournamentForm, ManagedUserForm, ScorerAssignmentForm,
    VenueForm,
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

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code != 200:
            return response
        match = Match.objects.filter(
            assigned_scorers=request.user,
            status__in=(Match.Status.LIVE, Match.Status.UPCOMING, Match.Status.INNINGS_BREAK),
        ).order_by('start_datetime').first()
        if match:
            return redirect('matches:match_scorer', slug=match.slug)
        return response


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

        return JsonResponse({'is_saved': is_saved, 'message': message})


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
        setting.site_name = request.POST.get('site_name', setting.site_name).strip()
        setting.site_tagline = request.POST.get('site_tagline', setting.site_tagline).strip()
        setting.primary_color = request.POST.get('primary_color', setting.primary_color).strip()
        setting.secondary_color = request.POST.get('secondary_color', setting.secondary_color).strip()
        setting.banner_title = request.POST.get('banner_title', setting.banner_title).strip()
        setting.banner_subtitle = request.POST.get('banner_subtitle', setting.banner_subtitle).strip()
        setting.footer_text = request.POST.get('footer_text', setting.footer_text).strip()
        setting.contact_email = request.POST.get('contact_email', setting.contact_email).strip()
        setting.contact_phone = request.POST.get('contact_phone', setting.contact_phone).strip()
        setting.address = request.POST.get('address', setting.address).strip()
        setting.facebook_url = request.POST.get('facebook_url', setting.facebook_url).strip()
        setting.twitter_url = request.POST.get('twitter_url', setting.twitter_url).strip()
        setting.instagram_url = request.POST.get('instagram_url', setting.instagram_url).strip()
        setting.youtube_url = request.POST.get('youtube_url', setting.youtube_url).strip()

        if 'logo' in request.FILES:
            setting.logo = request.FILES['logo']
        if 'favicon' in request.FILES:
            setting.favicon = request.FILES['favicon']
        if 'banner_image' in request.FILES:
            setting.banner_image = request.FILES['banner_image']

        setting.save()
        messages.success(request, 'Website branding and operational settings saved!')
        return redirect('dashboard:website_settings')
