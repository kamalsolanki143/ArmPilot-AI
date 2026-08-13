# ══════════════════════════════════════════════════════════════════════════════
# ArmPilot-AI — Build Automation
# ══════════════════════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
.PHONY: setup dev build test lint format benchmark optimize \
        docker-up docker-down clean install serve cli \
        help env-check backend frontend

# ── Configuration ────────────────────────────────────────────────────────────

PROJECT_ROOT := $(shell pwd)
BACKEND_DIR  := $(PROJECT_ROOT)/backend
FRONTEND_DIR := $(PROJECT_ROOT)
DOCKER_DIR   := $(PROJECT_ROOT)/docker
PYTHON       := python3
PIP          := pip3
NODE         := node
PNPM         := pnpm
UVICORN      := uvicorn
CLI          := $(PYTHON) -m app.cli.main

# ── Development ──────────────────────────────────────────────────────────────

help: ## Show this help message
	@echo "ArmPilot-AI — Available Commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

env-check: ## Verify environment is ready
	@echo "Checking prerequisites..."
	@$(PYTHON) --version >/dev/null 2>&1 || (echo "Error: python3 not found" && exit 1)
	@$(PIP) --version >/dev/null 2>&1 || (echo "Error: pip3 not found" && exit 1)
	@echo "  Python: $$($(PYTHON) --version 2>&1)"
	@echo "  pip: available"
	@if command -v $(NODE) >/dev/null 2>&1; then \
		echo "  Node.js: $$($(NODE) --version)"; \
	else \
		echo "  Node.js: not found (frontend skipped)"; \
	fi
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		echo "  pnpm: $$($(PNPM) --version)"; \
	else \
		echo "  pnpm: not found"; \
	fi

setup: env-check ## Install all dependencies (Python + Node)
	@echo ""
	@echo "Installing Python dependencies..."
	cd $(BACKEND_DIR) && $(PIP) install -r requirements.txt
	@echo "  Python dependencies installed."
	@if [ ! -f $(PROJECT_ROOT)/.env ] && [ -f $(PROJECT_ROOT)/.env.example ]; then \
		cp $(PROJECT_ROOT)/.env.example $(PROJECT_ROOT)/.env; \
		echo "  Created .env from .env.example"; \
	elif [ -f $(PROJECT_ROOT)/.env ]; then \
		echo "  .env already exists, skipping."; \
	fi
	@mkdir -p $(PROJECT_ROOT)/models $(PROJECT_ROOT)/data $(PROJECT_ROOT)/reports $(PROJECT_ROOT)/logs
	@echo "  Ensured directories: models/ data/ reports/ logs/"
	@if command -v $(PNPM) >/dev/null 2>&1; then \
		echo ""; \
		echo "Installing frontend dependencies..."; \
		cd $(FRONTEND_DIR) && $(PNPM) install; \
		echo "  Frontend dependencies installed."; \
	fi
	@echo ""
	@echo "Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Place .gguf model files in the models/ directory"
	@echo "  2. Run: make dev"
	@echo "  3. Visit: http://localhost:8000/docs"

install: setup ## Alias for setup

dev: ## Start development servers (frontend + backend)
	@echo "Starting ArmPilot-AI development servers..."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:8443"
	@echo ""
	cd $(BACKEND_DIR) && ($(UVICORN) main:app --host 0.0.0.0 --port 8000 --reload &); \
	cd $(FRONTEND_DIR) && ($(PNPM) dev &); \
	wait

build: ## Build the frontend for production
	@echo "Building frontend..."
	cd $(FRONTEND_DIR) && $(PNPM) build
	@echo "Build complete: dist/"

test: ## Run all tests
	@echo "Running Python tests..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v --tb=short

lint: ## Run linting on all code
	@echo "Linting Python..."
	cd $(BACKEND_DIR) && $(PYTHON) -m flake8 app/ --max-line-length=120 --ignore=E501,W503,E203
	@echo "Linting TypeScript..."
	cd $(FRONTEND_DIR) && $(PNPM) exec tsc --noEmit

format: ## Format all code
	@echo "Formatting frontend..."
	cd $(FRONTEND_DIR) && $(PNPM) format
	@echo "Formatting Python..."
	cd $(BACKEND_DIR) && $(PYTHON) -m black app/ --line-length 120
	cd $(BACKEND_DIR) && $(PYTHON) -m isort app/ --profile black

benchmark: ## Run benchmarks (model=NAME, threads=N, etc.)
	@echo "Running benchmarks..."
	cd $(BACKEND_DIR) && $(CLI) benchmark run \
		--model $(or $(model),llama-3.2-1b-instruct) \
		--threads $(or $(threads),4) \
		--batch-size $(or $(batch-size),512) \
		--num-requests $(or $(num-requests),10) \
		--max-tokens $(or $(max-tokens),128) \
		--concurrency $(or $(concurrency),1)

optimize: ## Run optimization sweep (model=NAME, objective=OBJ)
	@echo "Running optimization..."
	cd $(BACKEND_DIR) && $(CLI) optimize run \
		--model $(or $(model),llama-3.2-1b-instruct) \
		--objective $(or $(objective),throughput) \
		--max-candidates $(or $(max-candidates),8) \
		--benchmarks-per $(or $(benchmarks-per),5) \
		--max-tokens $(or $(max-tokens),128)

# ── Docker ───────────────────────────────────────────────────────────────────

docker-up: ## Start services via Docker Compose (dev)
	docker compose -f $(DOCKER_DIR)/docker-compose.yml up -d
	@echo "Services started. Visit http://localhost:8000/docs"

docker-down: ## Stop Docker Compose services
	docker compose -f $(DOCKER_DIR)/docker-compose.yml down

docker-build: ## Build production Docker image
	docker compose -f $(DOCKER_DIR)/docker-compose.prod.yml build

docker-logs: ## Tail Docker Compose logs
	docker compose -f $(DOCKER_DIR)/docker-compose.yml logs -f

# ── Production ───────────────────────────────────────────────────────────────

serve: ## Start production server
	@echo "Starting ArmPilot-AI production server..."
	cd $(BACKEND_DIR) && $(UVICORN) main:app \
		--host $(or $(host),0.0.0.0) \
		--port $(or $(port),8000) \
		--workers $(or $(workers),4) \
		--log-level info

# ── CLI ──────────────────────────────────────────────────────────────────────

cli: ## Run CLI commands (args="command subcommand ...")
	cd $(BACKEND_DIR) && $(CLI) $(args)

cli-info: ## Show installation and hardware info
	cd $(BACKEND_DIR) && $(CLI) info

cli-models: ## List available models
	cd $(BACKEND_DIR) && $(CLI) models

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts, caches, and temp files
	@echo "Cleaning build artifacts..."
	@find $(PROJECT_ROOT) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -maxdepth 3 -type d \( -name "*.egg-info" -o -name "dist" -o -name "build" -o -name ".eggs" \) -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(BACKEND_DIR)/htmlcov $(BACKEND_DIR)/.coverage 2>/dev/null || true
	@find $(PROJECT_ROOT) -maxdepth 3 -name "*.tmp" -o -name "*.bak" -o -name "*~" -o -name "*.swp" | xargs rm -f 2>/dev/null || true
	@echo "Clean complete."
