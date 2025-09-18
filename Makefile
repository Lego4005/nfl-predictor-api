# NFL Predictor API - Test Makefile
# Comprehensive testing and development utilities

.PHONY: help install test test-unit test-integration test-e2e test-ml test-performance test-security
.PHONY: test-frontend test-all lint format clean coverage start-services stop-services
.PHONY: docker-test docker-build docker-clean benchmark load-test regression-test
.PHONY: test-watch test-debug setup-dev setup-ci report-coverage

# Default target
help: ## Show this help message
	@echo "NFL Predictor API - Test Suite Commands"
	@echo "======================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Variables
PYTHON := python
PIP := pip
NPM := npm
PYTEST := pytest
DOCKER := docker
DOCKER_COMPOSE := docker-compose -f docker-compose.test.yml

# Test Configuration
PYTEST_ARGS := --tb=short --strict-markers --strict-config
COVERAGE_THRESHOLD := 80
PARALLEL_WORKERS := auto

# Environment Variables
export PYTHONPATH := $(shell pwd)/src
export ENVIRONMENT := test
export LOG_LEVEL := DEBUG
export DATABASE_URL := postgresql://test_user:test_password@localhost:5433/nfl_predictor_test
export REDIS_URL := redis://localhost:6380/0

###################
# Setup & Installation
###################

install: install-python install-node ## Install all dependencies
	@echo "✅ All dependencies installed"

install-python: ## Install Python dependencies
	@echo "🐍 Installing Python dependencies..."
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true
	@echo "✅ Python dependencies installed"

install-node: ## Install Node.js dependencies
	@echo "📦 Installing Node.js dependencies..."
	$(NPM) ci
	@echo "✅ Node.js dependencies installed"

install-dev: install ## Install development dependencies
	@echo "🛠️ Installing development tools..."
	$(PIP) install black isort flake8 mypy bandit safety pre-commit
	$(NPM) install --save-dev eslint prettier @typescript-eslint/parser
	pre-commit install
	@echo "✅ Development environment ready"

###################
# Code Quality
###################

lint: lint-python lint-frontend ## Run all linting
	@echo "✅ All linting completed"

lint-python: ## Run Python linting
	@echo "🔍 Running Python linting..."
	black --check src/ tests/ *.py
	isort --check-only src/ tests/ *.py
	flake8 src/ tests/ *.py --max-line-length=88 --extend-ignore=E203,W503
	mypy src/ --ignore-missing-imports
	@echo "✅ Python linting passed"

lint-frontend: ## Run frontend linting
	@echo "🔍 Running frontend linting..."
	npx tsc --noEmit
	# Add ESLint when configured: npx eslint src/**/*.{ts,tsx}
	@echo "✅ Frontend linting passed"

format: format-python format-frontend ## Format all code
	@echo "✅ All code formatted"

format-python: ## Format Python code
	@echo "🔧 Formatting Python code..."
	black src/ tests/ *.py
	isort src/ tests/ *.py
	@echo "✅ Python code formatted"

format-frontend: ## Format frontend code
	@echo "🔧 Formatting frontend code..."
	npx prettier --write "src/**/*.{ts,tsx,js,jsx,css,md}"
	@echo "✅ Frontend code formatted"

security: ## Run security checks
	@echo "🔒 Running security checks..."
	bandit -r src/ -f json -o reports/bandit-report.json
	safety check --json --output reports/safety-report.json
	@echo "✅ Security checks completed"

###################
# Test Execution
###################

test: test-unit ## Run default test suite (unit tests)

test-all: test-unit test-integration test-frontend test-ml ## Run all test suites
	@echo "🎉 All test suites completed!"

test-unit: ## Run unit tests with coverage
	@echo "🧪 Running unit tests..."
	$(PYTEST) tests/unit/ $(PYTEST_ARGS) \
		--cov=src \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-report=term-missing \
		--cov-fail-under=$(COVERAGE_THRESHOLD) \
		-n $(PARALLEL_WORKERS) \
		--dist worksteal
	@echo "✅ Unit tests completed"

test-integration: start-test-services ## Run integration tests
	@echo "🔗 Running integration tests..."
	$(PYTEST) tests/integration/ $(PYTEST_ARGS) \
		--cov=src \
		--cov-append \
		--maxfail=5
	@echo "✅ Integration tests completed"

test-e2e: start-test-services ## Run end-to-end tests
	@echo "🌐 Running E2E tests..."
	$(PYTEST) tests/e2e/ $(PYTEST_ARGS) \
		--maxfail=3 \
		--timeout=300
	@echo "✅ E2E tests completed"

test-ml: ## Run machine learning tests
	@echo "🤖 Running ML model tests..."
	$(PYTEST) tests/ml/ $(PYTEST_ARGS) \
		--cov=src/ml \
		--cov-append \
		--timeout=120
	@echo "✅ ML tests completed"

test-frontend: ## Run frontend tests
	@echo "⚛️ Running frontend tests..."
	$(NPM) run test -- --coverage --watchAll=false --ci
	npx vitest run --coverage
	@echo "✅ Frontend tests completed"

test-performance: start-test-services ## Run performance tests
	@echo "🚀 Running performance tests..."
	$(PYTEST) tests/performance/ $(PYTEST_ARGS) \
		--benchmark-only \
		--benchmark-json=reports/performance-results.json \
		--benchmark-columns=min,max,mean,stddev,rounds,iterations
	@echo "✅ Performance tests completed"

test-security: start-test-services ## Run security tests
	@echo "🔐 Running security tests..."
	$(PYTEST) tests/security/ $(PYTEST_ARGS) \
		--maxfail=5
	@echo "✅ Security tests completed"

test-watch: ## Run tests in watch mode
	@echo "👁️ Starting test watcher..."
	$(PYTEST) tests/unit/ $(PYTEST_ARGS) \
		--cov=src \
		--cov-report=term \
		-f \
		--tb=short

test-debug: ## Run tests with debugging enabled
	@echo "🐛 Running tests in debug mode..."
	$(PYTEST) tests/unit/ $(PYTEST_ARGS) \
		--pdb \
		--pdbcls=IPython.terminal.debugger:TerminalPdb \
		-s \
		-v

test-single: ## Run a single test file (usage: make test-single FILE=tests/unit/test_example.py)
	@echo "🎯 Running single test file: $(FILE)"
	$(PYTEST) $(FILE) $(PYTEST_ARGS) -v

test-marker: ## Run tests with specific marker (usage: make test-marker MARKER=slow)
	@echo "🏷️ Running tests with marker: $(MARKER)"
	$(PYTEST) -m $(MARKER) $(PYTEST_ARGS) -v

###################
# Load & Stress Testing
###################

load-test: start-test-services ## Run load tests with Locust
	@echo "📈 Running load tests..."
	@mkdir -p reports/load-test
	locust -f tests/load/locustfile.py \
		--headless \
		--users 50 \
		--spawn-rate 5 \
		--run-time 5m \
		--host http://localhost:8001 \
		--html reports/load-test/report.html \
		--csv reports/load-test/results
	@echo "✅ Load tests completed"

benchmark: ## Run performance benchmarks
	@echo "⚡ Running benchmarks..."
	@mkdir -p reports/benchmarks
	$(PYTEST) tests/performance/ $(PYTEST_ARGS) \
		--benchmark-only \
		--benchmark-json=reports/benchmarks/results.json \
		--benchmark-histogram=reports/benchmarks/histogram
	@echo "✅ Benchmarks completed"

stress-test: start-test-services ## Run stress tests
	@echo "💪 Running stress tests..."
	locust -f tests/stress/stressfile.py \
		--headless \
		--users 200 \
		--spawn-rate 10 \
		--run-time 10m \
		--host http://localhost:8001 \
		--html reports/stress-test/report.html
	@echo "✅ Stress tests completed"

regression-test: ## Run performance regression tests
	@echo "📊 Running regression tests..."
	python tests/utils/performance_regression.py \
		--current reports/performance-results.json \
		--baseline performance-baseline.json \
		--threshold 20 \
		--output reports/regression-report.html
	@echo "✅ Regression tests completed"

###################
# Docker Testing
###################

docker-test: docker-build-test ## Run tests in Docker
	@echo "🐳 Running tests in Docker..."
	$(DOCKER_COMPOSE) up --abort-on-container-exit test-runner
	$(DOCKER_COMPOSE) down

docker-build: ## Build Docker images for testing
	@echo "🔨 Building Docker test images..."
	$(DOCKER) build -t nfl-predictor-test:latest -f Dockerfile .
	$(DOCKER) build -t nfl-predictor-ml-test:latest -f Dockerfile.ml .
	@echo "✅ Docker images built"

docker-build-test: docker-build ## Build test-specific Docker images
	$(DOCKER_COMPOSE) build

docker-up: ## Start test services with Docker
	@echo "🚀 Starting test services..."
	$(DOCKER_COMPOSE) up -d test-postgres test-redis mock-apis
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@echo "✅ Test services started"

docker-down: ## Stop test services
	@echo "🛑 Stopping test services..."
	$(DOCKER_COMPOSE) down
	@echo "✅ Test services stopped"

docker-logs: ## Show Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-clean: docker-down ## Clean up Docker resources
	@echo "🧹 Cleaning Docker resources..."
	$(DOCKER) system prune -f
	$(DOCKER) volume prune -f
	@echo "✅ Docker cleanup completed"

###################
# Service Management
###################

start-services: start-test-services ## Alias for start-test-services

start-test-services: ## Start test database and Redis
	@echo "🚀 Starting test services..."
	$(DOCKER_COMPOSE) up -d test-postgres test-redis
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@$(DOCKER_COMPOSE) exec test-postgres pg_isready -U test_user -d nfl_predictor_test || sleep 5
	@$(DOCKER_COMPOSE) exec test-redis redis-cli ping || sleep 5
	@echo "✅ Test services are ready"

stop-services: stop-test-services ## Alias for stop-test-services

stop-test-services: ## Stop test services
	@echo "🛑 Stopping test services..."
	$(DOCKER_COMPOSE) stop test-postgres test-redis
	@echo "✅ Test services stopped"

restart-services: stop-test-services start-test-services ## Restart test services

status-services: ## Check service status
	@echo "📊 Service Status:"
	$(DOCKER_COMPOSE) ps

###################
# Coverage & Reporting
###################

coverage: test-unit ## Generate coverage report
	@echo "📊 Generating coverage report..."
	coverage html --directory=htmlcov
	coverage xml -o coverage.xml
	coverage report --show-missing
	@echo "✅ Coverage report generated"

coverage-open: coverage ## Open coverage report in browser
	@echo "🌐 Opening coverage report..."
	@python -m http.server 8080 --directory htmlcov &
	@echo "Coverage report available at http://localhost:8080"

report-coverage: ## Upload coverage to Codecov
	@echo "📤 Uploading coverage to Codecov..."
	codecov --file coverage.xml --flags backend
	@echo "✅ Coverage uploaded"

reports: ## Generate all test reports
	@echo "📋 Generating test reports..."
	@mkdir -p reports/{unit,integration,e2e,performance,security}
	@echo "✅ Report directories created"

clean-reports: ## Clean test reports
	@echo "🧹 Cleaning test reports..."
	@rm -rf reports/ htmlcov/ coverage.xml .coverage .pytest_cache/
	@rm -rf test-reports/ node_modules/.cache/
	@echo "✅ Reports cleaned"

###################
# CI/CD Helpers
###################

setup-ci: ## Setup CI environment
	@echo "⚙️ Setting up CI environment..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(NPM) ci
	@echo "✅ CI environment ready"

ci-test: ## Run CI test suite
	@echo "🤖 Running CI test suite..."
	$(MAKE) lint
	$(MAKE) security
	$(MAKE) test-unit
	$(MAKE) test-frontend
	$(MAKE) coverage
	@echo "✅ CI tests completed"

pre-commit: ## Run pre-commit checks
	@echo "✅ Running pre-commit checks..."
	pre-commit run --all-files

###################
# Utilities
###################

clean: clean-reports ## Clean all generated files
	@echo "🧹 Cleaning all generated files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@rm -rf .tox/ dist/ build/
	@echo "✅ Cleanup completed"

init-db: start-test-services ## Initialize test database
	@echo "🗄️ Initializing test database..."
	@sleep 5
	alembic upgrade head
	python scripts/seed_test_data.py
	@echo "✅ Test database initialized"

reset-db: ## Reset test database
	@echo "🔄 Resetting test database..."
	$(DOCKER_COMPOSE) exec test-postgres dropdb -U test_user nfl_predictor_test || true
	$(DOCKER_COMPOSE) exec test-postgres createdb -U test_user nfl_predictor_test
	$(MAKE) init-db
	@echo "✅ Database reset completed"

shell: ## Start interactive Python shell with app context
	@echo "🐚 Starting interactive shell..."
	python -c "
import sys;
sys.path.insert(0, 'src');
from main import app;
import IPython;
IPython.embed(header='NFL Predictor API Shell - App context loaded')
"

test-env: ## Show test environment information
	@echo "🌍 Test Environment Information:"
	@echo "Python Version: $(shell python --version)"
	@echo "Node Version: $(shell node --version)"
	@echo "Database URL: $(DATABASE_URL)"
	@echo "Redis URL: $(REDIS_URL)"
	@echo "Environment: $(ENVIRONMENT)"
	@echo "Coverage Threshold: $(COVERAGE_THRESHOLD)%"

###################
# Quick Commands
###################

quick: test-unit lint ## Quick test (unit tests + linting)

full: test-all lint security coverage ## Full test suite

dev: install-dev start-test-services ## Setup development environment

# Export variables for sub-makes
export