from django.apps import AppConfig

class PortalConfig(AppConfig):
    """Konfigurasi aplikasi Django `portal`; mewarisi AppConfig dari Django."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"
    verbose_name = "KREASI Portal"
