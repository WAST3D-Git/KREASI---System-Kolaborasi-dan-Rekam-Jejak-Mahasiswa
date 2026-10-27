from django.apps import AppConfig

class KreasiAppConfig(AppConfig):
    """Mendaftarkan aplikasi KREASI agar model dan konfigurasi ditemukan Django."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "kreasi_app"
    verbose_name = "KREASI - Kolaborasi dan Rekam Jejak Prestasi"
