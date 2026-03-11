.PHONY: help install run dev test lint format clean docker-up docker-down docker-build migrate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	uv sync

run: ## Run the application
	uv run python -m src.main

dev: ## Run the application in development mode
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint: ## Run linter
	uv run ruff check src/

format: ## Format code
	uv run ruff format src/

type-check: ## Run type checker
	uv run mypy src/

clean: ## Clean up build artifacts
	rm -rf .venv dist build *.egg-info __pycache__ .pytest_cache .mypy_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start all services
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## Show logs
	docker-compose logs -f

docker-ps: ## Show running containers
	docker-compose ps

migrate: ## Run database migrations
	uv run python -m src.data.migrations

db-shell: ## Open database shell
	docker-compose exec db psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

redis-shell: ## Open Redis shell
	docker-compose exec redis redis-cli

setup: install migrate ## Full setup (install + migrate)
	@echo 'Setup complete!'

check: lint type-check test ## Run all checks
