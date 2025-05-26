##############
# Конфигурация

create-env:
	@cp ./.env.example ./.env

#################################################
# Управление контейнерами для разработки локально

up:
	@docker compose -f docker-compose-dev.yml up --build -d

down:
	@docker compose -f docker-compose-dev.yml down

start:
	@docker compose -f docker-compose-dev.yml start

stop:
	@docker compose -f docker-compose-dev.yml stop

restart:
	@docker compose -f docker-compose-dev.yml restart

show-logs:
	@docker compose -f docker-compose-dev.yml logs

follow-logs:
	@docker compose -f docker-compose-dev.yml logs -f

###################
# Управление Django

make-migrations:
	@docker exec -it 3d-backend poetry run python manage.py makemigrations

show-migrations:
	@docker exec -it 3d-backend /app/docker/app/show-migrations.sh
	
rollback-migration:
	@docker exec -it 3d-backend /app/docker/app/rollback-migration.sh

migrate:
	@docker exec -it 3d-backend poetry run python manage.py migrate

create-superuser:
	@docker exec -it 3d-backend poetry run python manage.py createsuperuser

enter-backend:
	@docker exec -it 3d-backend bash