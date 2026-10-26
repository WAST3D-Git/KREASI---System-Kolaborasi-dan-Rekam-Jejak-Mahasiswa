from django.apps import AppConfig

class PortalConfig(AppConfig):
    """Konfigurasi aplikasi Django `portal` (didaftarkan di INSTALLED_APPS pada settings.py).
    OOP: PEWARISAN TUNGGAL dari `AppConfig`; hanya mengisi nama aplikasi dan jenis ID otomatis.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"
    verbose_name = "KREASI Portal"
