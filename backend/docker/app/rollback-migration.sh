#!/bin/bash

read -p "App name: " APP_NAME
read -p "Migration: " MIGRATION_NAME
poetry run python manage.py migrate $APP_NAME $MIGRATION_NAME
