from django.views.generic import ListView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q, F
from .models import CricketVideo, VideoCategory, VideoLike, VideoBookmark

class VideoListView(ListView):
    model = CricketVideo
    template_name = 'videos/video_list.html'
    context_object_name = 'videos'
    paginate_by = 12

    def get_queryset(self):
        qs = CricketVideo.objects.filter(is_active=True).select_related('category')
        cat_slug = self.request.GET.get('category')
        if cat_slug:
            qs = qs.filter(category__slug=cat_slug)
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = VideoCategory.objects.all()
        context['active_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['featured_video'] = CricketVideo.objects.filter(is_featured=True, is_active=True).first()
        return context


class VideoDetailView(DetailView):
    model = CricketVideo
    template_name = 'videos/video_detail.html'
    context_object_name = 'video'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        CricketVideo.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.object
        context['related_videos'] = CricketVideo.objects.filter(
            category=video.category, is_active=True
        ).exclude(id=video.id)[:6]

        user = self.request.user
        if user.is_authenticated:
            context['has_liked'] = VideoLike.objects.filter(video=video, user=user).exists()
            context['has_bookmarked'] = VideoBookmark.objects.filter(video=video, user=user).exists()
        else:
            context['has_liked'] = False
            context['has_bookmarked'] = False
        return context


class ToggleVideoLikeView(LoginRequiredMixin, View):
    def post(self, request, slug):
        video = get_object_or_404(CricketVideo, slug=slug)
        like, created = VideoLike.objects.get_or_create(video=video, user=request.user)

        if not created:
            like.delete()
            liked = False
            CricketVideo.objects.filter(pk=video.pk).update(likes_count=F('likes_count') - 1)
        else:
            liked = True
            CricketVideo.objects.filter(pk=video.pk).update(likes_count=F('likes_count') + 1)

        video.refresh_from_db()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'liked': liked, 'total_likes': video.likes_count})
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer) if referer else redirect('videos:video_detail', slug=slug)


class ToggleVideoBookmarkView(LoginRequiredMixin, View):
    def post(self, request, slug):
        video = get_object_or_404(CricketVideo, slug=slug)
        bookmark, created = VideoBookmark.objects.get_or_create(video=video, user=request.user)

        if not created:
            bookmark.delete()
            bookmarked = False
            message = 'Video removed from bookmarks'
        else:
            bookmarked = True
            message = 'Video saved to bookmarks'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'bookmarked': bookmarked, 'message': message})
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer) if referer else redirect('videos:video_detail', slug=slug)
