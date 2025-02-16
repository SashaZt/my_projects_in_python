.PHONY: up down build logs migrate-revision migrate-up clean start

# Запуск всего проекта
up:
	docker-compose up -d

# Остановка проекта
down:
	docker-compose down

# Сборка проекта
build:
	docker-compose build --no-cache

# Просмотр логов
logs:
	docker-compose logs -f

# Создание новой миграции
migrate-revision:
	@read -p "Enter migration name: " name; \
	docker-compose exec web alembic -c alembic.ini revision --autogenerate -m "$$name"

# Применение миграций
migrate-up:
	docker-compose exec web alembic -c alembic.ini upgrade head

# Полная пересборка
clean:
	docker-compose down -v
	rm -rf pgdata/*
	docker system prune -af
	docker-compose build --no-cache

# Запуск проекта с миграциями
start:
	docker-compose up -d postgres
	@echo "Waiting for PostgreSQL..."
	@sleep 10
	docker-compose up -d web
	@echo "Waiting for web service..."
	@sleep 20
	@echo "Checking web service status..."
	@if [ "$$(docker-compose ps -q web)" ]; then \
		if [ "$$(docker inspect -f '{{.State.Running}}' $$(docker-compose ps -q web))" = "true" ]; then \
			make migrate-up; \
			docker-compose up -d client; \
		else \
			echo "Web service failed to start"; \
			docker-compose logs web; \
			exit 1; \
		fi \
	else \
		echo "Web service not found"; \
		exit 1; \
	fi
	make logs
# Помощь по командам
help:
	@echo "Available commands:"
	@echo "  make start         - Start project with migrations"
	@echo "  make up           - Start containers"
	@echo "  make down         - Stop containers"
	@echo "  make build        - Rebuild containers"
	@echo "  make logs         - Show logs"
	@echo "  make migrate-revision - Create new migration"
	@echo "  make migrate-up   - Apply migrations"
	@echo "  make clean        - Full cleanup and rebuild"
	@echo "  make help         - Show this help"