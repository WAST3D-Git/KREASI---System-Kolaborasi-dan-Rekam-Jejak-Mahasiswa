"""Titik masuk WSGI: dipakai gunicorn/hosting untuk menjalankan aplikasi (lihat start.sh)."""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kreasi_project.settings")
application = get_wsgi_application()
