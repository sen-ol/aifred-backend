#!/usr/bin/env bash
set -o errexit
python manage.py migrate --no-input
python manage.py seed_preview
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --timeout 60 --access-logfile -
