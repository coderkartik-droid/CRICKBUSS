from rest_framework import serializers
from .models import NewsArticle, NewsCategory, ArticleComment

class NewsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsCategory
        fields = ['id', 'name', 'slug', 'description']

class ArticleCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_avatar = serializers.CharField(source='user.get_avatar_url', read_only=True)

    class Meta:
        model = ArticleComment
        fields = ['id', 'user_name', 'user_avatar', 'content', 'created_at', 'parent']
        read_only_fields = ['id', 'user_name', 'user_avatar', 'created_at']

class NewsArticleSerializer(serializers.ModelSerializer):
    category = NewsCategorySerializer(read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'slug', 'category', 'author_name_fallback',
            'image_url', 'excerpt', 'content', 'views_count', 'likes_count',
            'comments_count', 'is_breaking', 'is_trending', 'is_featured',
            'published_at'
        ]

class NewsArticleSimpleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.CharField(source='get_image_url', read_only=True)

    class Meta:
        model = NewsArticle
        fields = ['id', 'title', 'slug', 'category_name', 'image_url', 'excerpt', 'is_breaking', 'published_at']
