from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import PhotoAlbum

class PhotoAlbumListView(ListView):
    model = PhotoAlbum
    template_name = 'photos/photo_list.html'
    context_object_name = 'albums'
    paginate_by = 12

    def get_queryset(self):
        qs = PhotoAlbum.objects.filter(is_active=True).prefetch_related('photos')
        cat = self.request.GET.get('category')
        if cat and cat in PhotoAlbum.AlbumCategory.values:
            qs = qs.filter(category=cat)
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = PhotoAlbum.AlbumCategory.choices
        context['active_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class PhotoAlbumDetailView(DetailView):
    model = PhotoAlbum
    template_name = 'photos/album_detail.html'
    context_object_name = 'album'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.object
        context['photos'] = album.photos.all()
        context['other_albums'] = PhotoAlbum.objects.filter(is_active=True).exclude(id=album.id)[:4]
        return context
