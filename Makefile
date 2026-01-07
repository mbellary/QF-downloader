SHELL := /bin/sh
.DEFAULT_GOAL := help

# -------------------------------------------------------------------
# Project / Docker
# -------------------------------------------------------------------
PROJECT_NAME ?= qf-downloader
COMPOSE_FILE ?= docker-compose.yml
DOCKER_COMPOSE ?= docker compose

APP_SERVICE := qf_app
DEPS := localstack

# Runtime
APP_ENV ?= production

# Tooling
UV ?= uv
RUFF ?= $(UV) run --dev -- ruff

# All arguments after the first make target (e.g. after `run`)
ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

# -------------------------------------------------------------------
# Help
# -------------------------------------------------------------------
.PHONY: help
help:
	@echo ""
	@echo "QF Downloader – Development Commands"
	@echo "------------------------------------"
	@echo ""
	@echo "Stack lifecycle:"
	@echo "  make up                     Start dev dependencies (LocalStack, etc.)"
	@echo "  make down                   Stop dev stack"
	@echo "  make clean                  Stop stack + remove volumes"
	@echo ""
	@echo "Build:"
	@echo "  make build                  Build Docker images"
	@echo ""
	@echo "Run workers:"
	@echo "  make run <worker> -- <args>"
	@echo ""
	@echo "Examples:"
	@echo "  make run worker_historical -- backfill --provider-name dukascopy --years 3"
	@echo "  APP_ENV=localstack make run worker_incremental -- --providers-file config/vendors/fx_providers.json"
	@echo ""
	@echo "Code quality:"
	@echo "  make lint                   Ruff lint + format check"
	@echo "  make test                   Run full test suite (delegates to Makefile.test)"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs                   Tail logs from app container"
	@echo "  make shell                  Open a shell inside qf_app"
	@echo ""

# --------------------------------------------------
# CLI helpers (safe defaults)
# --------------------------------------------------
.PHONY: cli
cli:
	@if [ -z "$(ARGS)" ]; then \
		echo "❌ Usage: make cli <command> [args]"; exit 1; \
	fi
	APP_ENV=$(APP_ENV) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm \
	$(APP_SERVICE) sh -lc "uv run python -m qf_downloader.cli $(ARGS)"


# -------------------------------------------------------------------
# Build
# -------------------------------------------------------------------
.PHONY: build
build:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build

# -------------------------------------------------------------------
# Stack control
# -------------------------------------------------------------------
.PHONY: up
up:
	@echo "▶ Starting dev stack (APP_ENV=$(APP_ENV))"
	APP_ENV=$(APP_ENV) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d $(DEPS)

.PHONY: down
down:
	@echo "▶ Stopping dev stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

.PHONY: clean
clean:
	@echo "▶ Cleaning dev stack (containers + volumes)"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans

# -------------------------------------------------------------------
# Run workers (DX entrypoint)
# -------------------------------------------------------------------
.PHONY: run
run: build up
	@echo "▶ Running worker: $(ARGS)"
	APP_ENV=$(APP_ENV) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm \
	$(APP_SERVICE) sh -lc "uv run $(ARGS)"

# -------------------------------------------------------------------
# Logs
# -------------------------------------------------------------------
.PHONY: logs
logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f $(APP_SERVICE)

# -------------------------------------------------------------------
# Shell
# -------------------------------------------------------------------
.PHONY: shell
shell:
	APP_ENV=$(APP_ENV) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm \
	$(APP_SERVICE) sh

# --------------------------------------------------
# Lint (local dev, fast feedback)
# --------------------------------------------------
.PHONY: lint
lint:
	$(RUFF) check .
	$(RUFF) format --check .

# --------------------------------------------------
# Tests (delegate to existing Makefile.test)
# --------------------------------------------------
.PHONY: test
test:
	$(MAKE) -f Makefile.test all

# -------------------------------------------------------------------
# Makefile arg passthrough safety
# -------------------------------------------------------------------
%:
	@:
