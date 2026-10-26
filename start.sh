#!/usr/bin/env sh
# Perintah start minimal untuk hosting. Aman dijalankan di setiap deploy/restart.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput -v0
# Admin awal dibuat sekali (dilewati bila sudah ada) jika KREASI_ADMIN_PASSWORD diisi.
if [ -n "$KREASI_ADMIN_PASSWORD" ]; then
  python manage.py create_kreasi_admin --only-if-missing \
    --username "${KREASI_ADMIN_USERNAME:-admin}" \
    --name "${KREASI_ADMIN_NAME:-Administrator Program Studi}" </dev/null
fi
exec gunicorn kreasi_project.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}" --threads 4 \
  --timeout 60 --access-logfile -
