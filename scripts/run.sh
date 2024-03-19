#!/bin/sh
# Run script

set -e

python manage.py wait_for_db
python manage.py collectstatic --noinput  # Collects all static files into a single specified directory
python manage.py migrate

uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi