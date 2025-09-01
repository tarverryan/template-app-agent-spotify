# Spotify App Agent Template Makefile
# Industry-standard development workflow with comprehensive tooling
# 
# Available commands:
#   make help              - Show this help message
#   make install           - Install dependencies
#   make dev-setup         - Set up development environment
#   make test              - Run all tests
#   make lint              - Run code quality checks
#   make format            - Format code
#   make security          - Run security scans
#   make docker-build      - Build Docker image
#   make docker-run        - Run with Docker Compose
#   make clean             - Clean build artifacts
#   make docs              - Generate documentation
#   make release           - Create a new release

.PHONY: help build run stop logs test clean auth update-all analytics dashboard cli setup

# Default target
help:
	@echo "Spotify App Agent Template - Available Commands:"
	@echo ""
	@echo "Build and Deployment:"
	@echo "  build          Build the Docker container"
	@echo "  run            Start the bot in background"
	@echo "  run-fg         Start the bot in foreground"
	@echo "  stop           Stop the bot"
	@echo "  logs           View bot logs"
	@echo "  clean          Clean up containers and images"
	@echo ""
	@echo "Setup and Configuration:"
	@echo "  setup          Interactive setup wizard"
	@echo "  test           Test Spotify connection and configuration"
	@echo "  auth           Generate Spotify refresh token"
	@echo ""
	@echo "Manual Playlist Updates:"
	@echo "  update-playlist1    Update playlist1 manually"
	@echo "  update-playlist2    Update playlist2 manually"
	@echo "  update-playlist3    Update playlist3 manually"
	@echo "  update-playlist4    Update playlist4 manually"
	@echo "  update-all          Update all playlists"
	@echo ""
	@echo "Monitoring and Analytics:"
	@echo "  analytics      Run comprehensive analytics"
	@echo "  dashboard      Start the web dashboard"
	@echo "  status         Show bot status"
	@echo ""
	@echo "Maintenance:"
	@echo "  create-playlists Create missing playlists"
	@echo "  preseed        Fill all playlists with tracks"
	@echo "  backup         Create backup of bot data"
	@echo "  restore        Restore bot data from backup"

# Docker image and container names
IMAGE_NAME = spotify-app-agent-template
CONTAINER_NAME = spotify-app-agent-template

# Build the Docker container
build:
	@echo "Building Spotify App Agent Template container..."
	docker build -t $(IMAGE_NAME):latest .
	@echo "✅ Build complete!"

# Run the bot in background
run:
	@echo "Starting Spotify App Agent Template..."
	docker run -d \
		--name $(CONTAINER_NAME) \
		--restart unless-stopped \
		-v $(PWD)/config:/app/config \
		-v $(PWD)/state:/app/state \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/snapshots:/app/snapshots \
		-v $(PWD)/playlist_art:/app/playlist_art \
		--env-file .env \
		$(IMAGE_NAME):latest
	@echo "✅ Bot started! Check logs with 'make logs'"

# Run the bot in foreground (for debugging)
run-fg:
	@echo "Starting Spotify App Agent Template in foreground..."
	docker run --rm \
		--name $(CONTAINER_NAME)-fg \
		-v $(PWD)/config:/app/config \
		-v $(PWD)/state:/app/state \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/snapshots:/app/snapshots \
		-v $(PWD)/playlist_art:/app/playlist_art \
		--env-file .env \
		$(IMAGE_NAME):latest

# Stop the bot
stop:
	@echo "Stopping Spotify App Agent Template..."
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	@echo "✅ Bot stopped!"

# View bot logs
logs:
	@echo "Viewing bot logs..."
	docker logs -f $(CONTAINER_NAME) || echo "Container not running. Start with 'make run'"

# Test Spotify connection and configuration
test:
	@echo "Testing Spotify connection and configuration..."
	docker run --rm \
		-v $(PWD)/config:/app/config \
		-v $(PWD)/state:/app/state \
		--env-file .env \
		$(IMAGE_NAME):latest python tools/test_bot.py

# Interactive setup wizard
setup:
	@echo "Running interactive setup wizard..."
	python tools/cli.py setup

# Generate Spotify refresh token
auth:
	@echo "Generating Spotify refresh token..."
	python scripts/get_spotify_token.py

# Manual playlist updates
update-playlist1:
	docker exec $(CONTAINER_NAME) python -c "from app.main import SpotifyBot; bot = SpotifyBot(); bot.run_manual_update('playlist1')"

update-playlist2:
	docker exec $(CONTAINER_NAME) python -c "from app.main import SpotifyBot; bot = SpotifyBot(); bot.run_manual_update('playlist2')"

update-playlist3:
	docker exec $(CONTAINER_NAME) python -c "from app.main import SpotifyBot; bot = SpotifyBot(); bot.run_manual_update('playlist3')"

update-playlist4:
	docker exec $(CONTAINER_NAME) python -c "from app.main import SpotifyBot; bot = SpotifyBot(); bot.run_manual_update('playlist4')"

# Update all playlists
update-all:
	@echo "Updating all playlists..."
	python tools/preseed_playlists.py

# Run analytics
analytics:
	@echo "Running comprehensive analytics..."
	python tools/analytics.py --report --visualize

# Start web dashboard
dashboard:
	@echo "Starting web dashboard..."
	python tools/web_dashboard.py

# Show bot status
status:
	@echo "Showing bot status..."
	python tools/cli.py status

# Create missing playlists
create-playlists:
	@echo "Creating missing playlists..."
	python tools/create_missing_playlists.py

# Preseed all playlists with tracks
preseed:
	@echo "Preseeding all playlists with tracks..."
	python tools/preseed_playlists.py

# Clean up containers and images
clean:
	@echo "Cleaning up containers and images..."
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME):latest || true
	@echo "✅ Cleanup complete!"

# Development commands
dev-install:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt

dev-run:
	@echo "Running bot in development mode..."
	python -m app.main

dev-test:
	@echo "Running tests..."
	python -m pytest tests/

# Database commands
init-db:
	@echo "Initializing database..."
	python tools/init_database.py

reset-db:
	@echo "Resetting database..."
	python tools/init_database.py --reset

# Health check
health:
	@echo "Checking bot health..."
	docker exec $(CONTAINER_NAME) python -c "import requests; print('Bot is healthy!')" || echo "Bot health check failed"

# Backup data
backup:
	@echo "Creating backup of bot data..."
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz state/ snapshots/ logs/
	@echo "✅ Backup created!"

# Restore data
restore:
	@echo "Restoring bot data from backup..."
	@read -p "Enter backup filename: " backup_file; \
	tar -xzf $$backup_file
	@echo "✅ Data restored!"

# CLI shortcuts
cli-setup:
	@echo "Running CLI setup..."
	python tools/cli.py setup

cli-test:
	@echo "Running CLI test..."
	python tools/cli.py test

cli-start:
	@echo "Starting bot via CLI..."
	python tools/cli.py start

cli-stop:
	@echo "Stopping bot via CLI..."
	python tools/cli.py stop

cli-status:
	@echo "Showing status via CLI..."
	python tools/cli.py status

cli-logs:
	@echo "Showing logs via CLI..."
	python tools/cli.py logs

cli-config:
	@echo "Showing configuration via CLI..."
	python tools/cli.py config

cli-edit:
	@echo "Editing configuration via CLI..."
	python tools/cli.py edit

cli-dashboard:
	@echo "Opening dashboard via CLI..."
	python tools/cli.py dashboard

# Analytics shortcuts
analytics-performance:
	@echo "Running performance analytics..."
	python tools/analytics.py --performance

analytics-playlists:
	@echo "Running playlist analytics..."
	python tools/analytics.py --playlists

analytics-trends:
	@echo "Running popularity trends analysis..."
	python tools/analytics.py --trends

analytics-genres:
	@echo "Running genre analysis..."
	python tools/analytics.py --genres

analytics-report:
	@echo "Generating analytics report..."
	python tools/analytics.py --report

analytics-viz:
	@echo "Creating analytics visualizations..."
	python tools/analytics.py --visualize

# Quick start sequence
quick-start:
	@echo "🚀 Quick Start Sequence"
	@echo "========================"
	@echo "1. Setting up bot..."
	@make setup
	@echo "2. Testing connection..."
	@make test
	@echo "3. Starting bot..."
	@make run
	@echo "4. Opening dashboard..."
	@make dashboard
	@echo "✅ Quick start complete!"

# Development workflow
dev-workflow:
	@echo "🛠️  Development Workflow"
	@echo "========================"
	@echo "1. Installing dependencies..."
	@make dev-install
	@echo "2. Running tests..."
	@make dev-test
	@echo "3. Starting in development mode..."
	@make dev-run
	@echo "✅ Development workflow complete!"

# =============================================================================
# INDUSTRY STANDARD COMMANDS
# =============================================================================

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

# Development setup
dev-setup:
	@echo "🛠️  Setting up development environment..."
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install
	@echo "✅ Development environment ready!"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest -v --cov=app --cov=tools --cov-report=html --cov-report=term
	@echo "✅ Tests complete!"

# Code quality checks
lint:
	@echo "🔍 Running code quality checks..."
	black --check .
	isort --check-only .
	flake8 .
	mypy app/ tools/ --ignore-missing-imports
	@echo "✅ Linting complete!"

# Format code
format:
	@echo "🎨 Formatting code..."
	black .
	isort .
	@echo "✅ Code formatted!"

# Security scans
security:
	@echo "🔒 Running security scans..."
	bandit -r app/ tools/
	safety check
	@echo "✅ Security scan complete!"

# Docker operations
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t $(IMAGE_NAME):latest .
	@echo "✅ Docker image built!"

docker-run:
	@echo "🐳 Running with Docker Compose..."
	docker-compose up -d
	@echo "✅ Services started!"

docker-test:
	@echo "🐳 Running tests in Docker..."
	docker-compose run --rm test
	@echo "✅ Docker tests complete!"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	sphinx-build -b html docs/source docs/build/html
	@echo "✅ Documentation generated!"

docs-serve:
	@echo "📚 Serving documentation..."
	python -m http.server 8000 --directory docs/build/html
	@echo "✅ Documentation served at http://localhost:8000"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	docker system prune -f
	@echo "✅ Cleanup complete!"

# Release management
release:
	@echo "🚀 Creating release..."
	@read -p "Enter version (e.g., 1.0.0): " version; \
	git tag -a v$$version -m "Release v$$version"; \
	git push origin v$$version; \
	@echo "✅ Release v$$version created!"

release-patch:
	@echo "🚀 Creating patch release..."
	@read -p "Enter patch version: " patch; \
	git tag -a v1.0.$$patch -m "Patch release v1.0.$$patch"; \
	git push origin v1.0.$$patch; \
	@echo "✅ Patch release v1.0.$$patch created!"

release-minor:
	@echo "🚀 Creating minor release..."
	@read -p "Enter minor version: " minor; \
	git tag -a v1.$$minor.0 -m "Minor release v1.$$minor.0"; \
	git push origin v1.$$minor.0; \
	@echo "✅ Minor release v1.$$minor.0 created!"

release-major:
	@echo "🚀 Creating major release..."
	@read -p "Enter major version: " major; \
	git tag -a v$$major.0.0 -m "Major release v$$major.0.0"; \
	git push origin v$$major.0.0; \
	@echo "✅ Major release v$$major.0.0 created!"

# CI/CD helpers
ci-test:
	@echo "🔄 Running CI tests..."
	pytest --cov=app --cov=tools --cov-report=xml --cov-report=html
	black --check .
	isort --check-only .
	flake8 .
	mypy app/ tools/ --ignore-missing-imports
	bandit -r app/ tools/
	@echo "✅ CI tests complete!"

ci-build:
	@echo "🔄 Building in CI..."
	docker build -t $(IMAGE_NAME):ci .
	@echo "✅ CI build complete!"

# Monitoring and observability
monitoring:
	@echo "📊 Starting monitoring stack..."
	docker-compose up -d prometheus grafana
	@echo "✅ Monitoring stack started!"
	@echo "📈 Prometheus: http://localhost:9090"
	@echo "📊 Grafana: http://localhost:3000 (admin/admin)"

# Performance testing
perf-test:
	@echo "⚡ Running performance tests..."
	python -m pytest tests/ -m "perf" -v
	@echo "✅ Performance tests complete!"

# Load testing
load-test:
	@echo "🔥 Running load tests..."
	python tools/load_test.py
	@echo "✅ Load tests complete!"

# Database operations
db-migrate:
	@echo "🗄️  Running database migrations..."
	python tools/migrate.py
	@echo "✅ Database migrations complete!"

db-seed:
	@echo "🌱 Seeding database..."
	python tools/seed.py
	@echo "✅ Database seeded!"

# Backup and restore
backup-full:
	@echo "💾 Creating full backup..."
	tar -czf backup-full-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		state/ snapshots/ logs/ config/ data/
	@echo "✅ Full backup created!"

restore-full:
	@echo "📥 Restoring full backup..."
	@read -p "Enter backup filename: " backup_file; \
	tar -xzf $$backup_file
	@echo "✅ Full backup restored!"

# Health checks
health-full:
	@echo "🏥 Running comprehensive health check..."
	@make health
	@make test
	@make lint
	@make security
	@echo "✅ Health check complete!"

# Development shortcuts
dev-lint:
	@echo "🔍 Running development linting..."
	black --check .
	isort --check-only .
	@echo "✅ Development linting complete!"

dev-format:
	@echo "🎨 Formatting code for development..."
	black .
	isort .
	@echo "✅ Code formatted for development!"

dev-security:
	@echo "🔒 Running development security scan..."
	bandit -r app/ tools/ -f json -o bandit-report.json
	@echo "✅ Development security scan complete!"

# Production helpers
prod-deploy:
	@echo "🚀 Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production deployment complete!"

prod-rollback:
	@echo "🔄 Rolling back production..."
	docker-compose -f docker-compose.prod.yml down
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✅ Production rollback complete!"

# =============================================================================
# END INDUSTRY STANDARD COMMANDS
# =============================================================================
