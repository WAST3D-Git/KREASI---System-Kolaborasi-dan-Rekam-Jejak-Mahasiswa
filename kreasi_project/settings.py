"""Konfigurasi Django untuk KREASI (simulasi/uji coba).

Variabel lingkungan (semuanya opsional; lihat .env.example):
  DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS,
  DB_NAME, DJANGO_MEDIA_ROOT, DJANGO_HTTPS (1 = cookie secure, default 1 saat DEBUG=0).
Pada hosting, arahkan DB_NAME dan DJANGO_MEDIA_ROOT ke volume/direktori persisten.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default):
    return os.environ.get(name, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# Default aman: DEBUG mati. Aktifkan lokal dengan DJANGO_DEBUG=1.
DEBUG = env_bool("DJANGO_DEBUG", False)

DB_PATH = Path(os.environ.get("DB_NAME", str(BASE_DIR / "db.sqlite3")))


def _load_secret_key():
    """Gunakan env bila ada; jika tidak, buat sekali lalu simpan di samping database
    agar sesi login tidak terputus setiap restart/redeploy."""
    key = os.environ.get("DJANGO_SECRET_KEY", "").strip()
    if key:
        return key
    if DEBUG:
        return "dev-only-insecure-key"
    key_file = DB_PATH.parent / ".kreasi_secret_key"
    try:
        if key_file.exists():
            saved = key_file.read_text().strip()
            if saved:
                return saved
        from django.core.management.utils import get_random_secret_key
        key = get_random_secret_key()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(key)
        try:
            key_file.chmod(0o600)
        except OSError:
            pass
        return key
    except OSError:
        from django.core.management.utils import get_random_secret_key
        return get_random_secret_key()


SECRET_KEY = _load_secret_key()

# Tanpa DJANGO_ALLOWED_HOSTS, terima semua host (cukup untuk simulasi di balik proxy hosting).
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost" if DEBUG else "*")
# Diperlukan Django >= 4 agar POST (login/simpan) lolos CSRF di balik HTTPS proxy.
# Contoh: DJANGO_CSRF_TRUSTED_ORIGINS=https://contoh.domain.id
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# Daftar komponen Django yang aktif. "portal" adalah aplikasi KREASI buatan sendiri.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "portal.apps.PortalConfig",
]

# Middleware = lapisan pemeriksa yang dilewati SETIAP permintaan (urut dari atas):
# keamanan, static, sesi login, CSRF (anti pemalsuan permintaan), autentikasi, dll.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # melayani static (CSS admin) tanpa nginx
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "kreasi_project.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "kreasi_project.wsgi.application"
ASGI_APPLICATION = "kreasi_project.asgi.application"

# Database: SQLite (satu file) secara bawaan. Lokasinya diatur lewat DB_NAME.
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": str(DB_PATH),
    }
}
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    # IMMEDIATE: transaksi tulis mengunci di awal sehingga baca-ubah-simpan state oleh
    # beberapa pengguna bersamaan tidak saling menimpa / "database is locked".
    # WAL: pembaca tidak terblokir penulis. timeout: tunggu antrean kunci (detik).
    DATABASES["default"]["OPTIONS"] = {
        "transaction_mode": "IMMEDIATE",
        "timeout": 20,
        "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
    }

# Mengarahkan mekanisme auth Django ke model akun KREASI yang memperluas AbstractUser.
AUTH_USER_MODEL = "portal.PortalUser"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
# Bahasa Indonesia dan zona waktu Makassar (WITA) untuk tanggal/waktu.
LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Makassar"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Non-manifest: tidak gagal bila collectstatic belum dijalankan.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
# UploadedDocument.file menempatkan berkas fisik di MEDIA_ROOT; metadata disimpan di DB.
# Berkas hanya dilayani lewat view berizin (/api/documents/<id>/), bukan URL publik.
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", str(BASE_DIR / "media")))
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024

# Cookie sesi tidak bisa dibaca JavaScript (mengurangi risiko pencurian sesi).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
if not DEBUG:
    # Hosting umumnya mengakhiri TLS di proxy; percayai header X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True
    _https = env_bool("DJANGO_HTTPS", True)
    SESSION_COOKIE_SECURE = _https
    CSRF_COOKIE_SECURE = _https
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
