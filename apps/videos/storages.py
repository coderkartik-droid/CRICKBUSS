"""Storage backend used for video files uploaded through the admin portal.

The project keeps its media on Cloudinary when Cloudinary is configured (see
the ``CLOUDINARY_STORAGE`` block in ``crickbuss.settings``).  Cloudinary's
regular media backend uploads every file as an ``image`` resource, and
Cloudinary rejects video files for that resource type.  Uploaded videos
therefore have to use the ``video`` resource type instead.

``video_storage`` is intentionally a callable: ``FileField`` accepts a callable
storage and resolves it from the settings that are actually active, so the
project keeps using the storage system it is already configured with instead of
one hard-coded at import time.
"""

from django.conf import settings

VIDEO_CLOUDINARY_BACKEND = 'cloudinary_storage.storage.VideoMediaCloudinaryStorage'


def _configured_media_backend():
    """Return the dotted path of the media storage backend currently in effect.

    Django configures media storage through the ``STORAGES`` setting.  The
    older ``DEFAULT_FILE_STORAGE`` setting is still read as a fallback so this
    helper also works on a Django older than 5.1.
    """
    storages_setting = getattr(settings, 'STORAGES', None) or {}
    default_backend = (storages_setting.get('default') or {}).get('BACKEND')
    if default_backend:
        return default_backend
    return str(getattr(settings, 'DEFAULT_FILE_STORAGE', '') or '')


def video_storage():
    """Return the storage object that should be used for uploaded video files.

    When the project is configured to serve media from Cloudinary, the video
    resource type is used so Cloudinary accepts the file.  Otherwise the
    project's already configured default media storage is returned unchanged.
    """
    from django.core.files.storage import storages
    from django.utils.module_loading import import_string

    if 'cloudinary' in _configured_media_backend().lower():
        return import_string(VIDEO_CLOUDINARY_BACKEND)()
    return storages['default']
