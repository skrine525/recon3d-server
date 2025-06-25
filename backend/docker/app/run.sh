#!/bin/bash

if [ "$1" = "-d" ] || [ "$1" = "--dev" ]; then
    poetry run python manage.py collectstatic --noinput
    poetry run python manage.py runserver 0.0.0.0:80
else
    while ! < /dev/tcp/$DATABASE_HOST/$DATABASE_PORT; do sleep 1; done;
    poetry run python manage.py migrate
    poetry run gunicorn core.wsgi -b 0.0.0.0:80 --workers=1
fi
