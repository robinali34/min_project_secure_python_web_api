.PHONY: help install test lint format security clean docker-build docker-run docker-test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-pre-commit: ## Install pre-commit hooks
	pre-commit install

test: ## Run tests
	python -m pytest tests/ -v

test-coverage: ## Run tests with coverage
	python -m pytest tests/ -v --cov=app --cov-report=xml --cov-report=html

test-security: ## Run security tests
	python -m pytest tests/test_security.py -v

lint: ## Run linting
	flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 app/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code
	black app/ tests/
	isort app/ tests/

format-check: ## Check code formatting
	black --check app/ tests/
	isort --check-only app/ tests/

type-check: ## Run type checking
	mypy app/ --ignore-missing-imports --no-strict-optional

security: ## Run security scans
	bandit -r app/ -ll
	pip-audit -r requirements.txt || true

security-full: ## Run comprehensive security scans
	bandit -r app/ -ll
	pip-audit -r requirements.txt || true
	semgrep --config=auto app/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf *.db
	rm -rf *.sqlite

docker-build: ## Build Docker image
	docker build -t secure-python-web-api .

docker-run: ## Run Docker container
	docker run -p 8000:8000 secure-python-web-api

docker-test: ## Run tests in Docker
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

docker-dev: ## Run development environment with Docker Compose
	docker-compose up --build

docker-stop: ## Stop Docker containers
	docker-compose down

setup-dev: install install-pre-commit ## Set up development environment
	@echo "Development environment set up successfully!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to check code quality"
	@echo "Run 'make format' to format code"

ci: test lint security ## Run CI pipeline locally
	@echo "CI pipeline completed successfully!"

all: clean install test lint security ## Run all checks
	@echo "All checks completed successfully!"
