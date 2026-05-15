.PHONY: help up build down delete up-build logs logs-api logs-db migrate local-migrate test test-unit test-integration test-e2e

help:
	@echo "Доступные команды:"
	@echo "  make up                - поднять контейнеры"
	@echo "  make build             - собрать контейнеры"
	@echo "  make down              - остановить контейнеры"
	@echo "  make delete            - остановить контейнеры с удаление томов"
	@echo "  make up-build          - собрать и поднять контейнеры"
	@echo "  make logs              - логи всех контейнеров"
	@echo "  make logs-api          - логи api"
	@echo "  make logs-db           - логи postgres"
	@echo "  make migrate           - запустить миграции"
	@echo "  make local-migrate     - запустить локальную миграцию"
	@echo "  make test              - все тесты"
	@echo "  make test-unit         - unit тесты"
	@echo "  make test-integration  - integration тесты"
	@echo "  make test-e2e          - e2e тесты"

up:
	docker compose up -d

build:
	docker compose build

down:
	docker compose down

delete:
	docker compose down -v

up-build:
	docker compose up -d --build

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-db:
	docker compose logs -f postgres

migrate:
	docker compose exec api alembic upgrade head

local-migrate:
	poetry run alembic upgrade head

test:
	poetry run pytest -v

test-unit:
	poetry run pytest tests/unit/ -v

test-integration:
	poetry run pytest tests/integration/ -v

test-e2e:
	poetry run pytest tests/e2e/ -v