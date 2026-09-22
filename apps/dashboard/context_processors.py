from .models import SiteSetting

def site_settings(request):
    """
    Exposes site_setting globally to all Django templates.
    """
    try:
        settings_obj = SiteSetting.get_settings()
    except Exception:
        settings_obj = None
    return {
        'site_setting': settings_obj
    }
