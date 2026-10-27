"""Titik masuk ASGI untuk server aplikasi."""
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kreasi_site.settings")
application = get_asgi_application()
