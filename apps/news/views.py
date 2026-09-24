from django.views.generic import ListView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q, F
from django.contrib import messages
from .models import NewsArticle, NewsCategory, ArticleComment, ArticleLike, ArticleBookmark

class NewsListView(ListView):
    model = NewsArticle
    template_name = 'news/news_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        qs = NewsArticle.objects.filter(is_published=True).select_related('category', 'author')
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        filter_type = self.request.GET.get('type')
        if filter_type == 'breaking':
            qs = qs.filter(is_breaking=True)
        elif filter_type == 'trending':
            qs = qs.filter(is_trending=True)

        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query))

        return qs.order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = NewsCategory.objects.all()
        context['active_category'] = self.request.GET.get('category', '')
        context['active_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['breaking_news'] = NewsArticle.objects.filter(is_breaking=True, is_published=True)[:5]
        return context


class NewsDetailView(DetailView):
    model = NewsArticle
    template_name = 'news/news_detail.html'
    context_object_name = 'article'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # Increment views counter atomically
        NewsArticle.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        context['comments'] = article.comments.filter(is_approved=True, parent__isnull=True).select_related('user').prefetch_related('replies__user')
        context['related_articles'] = NewsArticle.objects.filter(
            category=article.category, is_published=True
        ).exclude(id=article.id)[:4]

        # Check if current user has liked or bookmarked
        user = self.request.user
        if user.is_authenticated:
            context['has_liked'] = ArticleLike.objects.filter(article=article, user=user).exists()
            context['has_bookmarked'] = ArticleBookmark.objects.filter(article=article, user=user).exists()
        else:
            context['has_liked'] = False
            context['has_bookmarked'] = False

        return context


class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(NewsArticle, slug=slug, is_published=True)
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id')

        if content:
            parent = None
            if parent_id:
                parent = ArticleComment.objects.filter(id=parent_id, article=article).first()

            ArticleComment.objects.create(
                article=article,
                user=request.user,
                parent=parent,
                content=content
            )
            messages.success(request, 'Your comment was posted successfully!')
        else:
            messages.error(request, 'Comment cannot be empty.')

        return redirect('news:article_detail', slug=slug)


class ToggleLikeView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(NewsArticle, slug=slug)
        like, created = ArticleLike.objects.get_or_create(article=article, user=request.user)

        if not created:
            like.delete()
            liked = False
            NewsArticle.objects.filter(pk=article.pk).update(likes_count=F('likes_count') - 1)
        else:
            liked = True
            NewsArticle.objects.filter(pk=article.pk).update(likes_count=F('likes_count') + 1)

        article.refresh_from_db()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'liked': liked, 'total_likes': article.likes_count})
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer) if referer else redirect('news:article_detail', slug=slug)


class ToggleBookmarkView(LoginRequiredMixin, View):
    def post(self, request, slug):
        article = get_object_or_404(NewsArticle, slug=slug)
        bookmark, created = ArticleBookmark.objects.get_or_create(article=article, user=request.user)

        if not created:
            bookmark.delete()
            bookmarked = False
            message = 'Removed from bookmarks'
        else:
            bookmarked = True
            message = 'Article saved to bookmarks'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'bookmarked': bookmarked, 'message': message})
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer) if referer else redirect('news:article_detail', slug=slug)
