# Локальный запуск проекта через `docker-compose-loc.yml`

## Предварительные требования

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- Клонирован репозиторий проекта

## Шаги запуска

1. **Перейдите в корень проекта:**

   ```bash
   cd /путь/к/вашему/проекту
   ```

2. **Создайте файл окружения:**

   Выполните команду:

   ```bash
   make create-env
   ```

   После этого в корне появится файл `.env`. При необходимости отредактируйте его.

3. **Постройте и запустите контейнеры:**

   ```bash
   docker compose -f docker-compose-loc.yml up --build
   ```

4. **Примените миграции и создайте суперпользователя:**

   ```bash
   docker compose -f docker-compose-loc.yml exec backend python manage.py migrate
   docker compose -f docker-compose-loc.yml exec backend python manage.py createsuperuser
   ```

5. **Доступ к сервисам:**

   - Бэкенд: [http://localhost:8000/](http://localhost:8000/)
   - Админка: [http://localhost:8000/admin/](http://localhost:8000/admin/)

6. **Остановка контейнеров:**

   ```bash
   docker compose -f docker-compose-loc.yml down
   ```

## Полезные команды

- Просмотр логов:

  ```bash
  docker compose -f docker-compose-loc.yml logs -f
  ```

- Войти в контейнер:

  ```bash
  docker compose -f docker-compose-loc.yml exec backend bash
  ```

---

Если у вас есть дополнительные сервисы или переменные окружения, добавьте их в соответствующие разделы README. 