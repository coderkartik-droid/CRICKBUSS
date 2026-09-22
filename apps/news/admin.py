from django.contrib import admin
from .models import NewsCategory, NewsArticle, ArticleComment, ArticleLike, ArticleBookmark

@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author_name_fallback', 'views_count', 'likes_count', 'is_breaking', 'is_trending', 'is_featured', 'is_published', 'published_at')
    list_filter = ('category', 'is_breaking', 'is_trending', 'is_featured', 'is_published')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_breaking', 'is_trending', 'is_featured', 'is_published')
    ordering = ('-published_at',)

@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__email', 'article__title', 'content')
    list_editable = ('is_approved',)

admin.site.register(ArticleLike)
admin.site.register(ArticleBookmark)
