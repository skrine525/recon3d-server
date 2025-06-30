#!/bin/bash

set -e

if [ "$1" = "-d" ] || [ "$1" = "--dev" ]; then
    poetry run python manage.py collectstatic --noinput
    exec poetry run python manage.py runserver 0.0.0.0:80

elif [ "$1" = "celery" ]; then
    while ! < /dev/tcp/$DATABASE_HOST/$DATABASE_PORT; do sleep 1; done;

    WORKERS_COUNT=${CELERY_WORKERS:-1}
    exec poetry run celery -A core worker -l info --concurrency=${WORKERS_COUNT}

else
    while ! < /dev/tcp/$DATABASE_HOST/$DATABASE_PORT; do sleep 1; done;
    poetry run python manage.py migrate
    exec poetry run gunicorn core.wsgi -b 0.0.0.0:80 --workers=${GUNICORN_WORKERS} --timeout 60
fi
