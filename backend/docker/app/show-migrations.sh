#!/bin/bash

read -p "App name: " APP_NAME;
poetry run python manage.py showmigrations $APP_NAME
