###############
# Базовый образ

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Устанавливаем poetry окружение
COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN pip install poetry==2.0.0
RUN poetry install

# Установка пакетов
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 tesseract-ocr

# Перемещаем ресурсы контейнера
COPY ./docker/app ./docker/app

# Настраиваем права
RUN chmod +x ./docker/app/run.sh
RUN chmod +x ./docker/app/show-migrations.sh
RUN chmod +x ./docker/app/rollback-migration.sh

# Настраиваем рабочую директорию и точку входа
ENTRYPOINT ["/app/docker/app/run.sh"]
WORKDIR /app/core

##############
# Боевой образ

FROM base AS app

# Переносим исходный код Django проекта
COPY ./core .

#################################
# Образ сборки статических файлов
 
FROM app AS build-static

RUN poetry run python manage.py collectstatic --noinput

##########################
# Образ статических файлов

FROM nginx:1.27.5-alpine AS static

RUN rm -rf /usr/share/nginx/*
COPY --from=build-static /app/core/staticfiles /usr/share/nginx
COPY ./docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf
