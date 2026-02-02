SHELL := /bin/sh
.DEFAULT_GOAL := help

# --------------------------------------------------
# Environment
# --------------------------------------------------
ENV_FILE := .env.dev

ifneq (,$(wildcard $(ENV_FILE)))
	include $(ENV_FILE)
	export
endif

# --------------------------------------------------
# Runtime
# --------------------------------------------------
APP_ENV ?= localstack

ifeq ($(APP_ENV),localstack)
	USE_LOCALSTACK := true
endif


# --------------------------------------------------
# Docker
# --------------------------------------------------
COMPOSE_FILE ?= docker-compose.yml
DOCKER_COMPOSE := docker compose

APP_SERVICE := qf-app
DEPS := localstack

# --------------------------------------------------
# Tooling
# --------------------------------------------------
UV ?= uv
RUFF ?= $(UV) run --dev -- ruff

ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))

# --------------------------------------------------
# Help
# --------------------------------------------------
.PHONY: help
help:
	@echo ""
	@echo "QF Downloader – Development Commands"
	@echo "-----------------------------------"
	@echo ""
	@echo "Stack:"
	@echo "  make up              Start dev stack"
	@echo "  make down            Stop dev stack"
	@echo "  make clean           Remove stack + volumes"
	@echo ""
	@echo "Run:"
	@echo "  APP_ENV=localstack make run <cmd> -- <args>"
	@echo ""
	@echo "Quality:"
	@echo "  make lint"
	@echo "  make test"
	@echo ""

# --------------------------------------------------
# Build
# --------------------------------------------------
.PHONY: build
build:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) build

# --------------------------------------------------
# Stack lifecycle
# --------------------------------------------------
.PHONY: up
up:
	@echo "▶ Starting dev stack (APP_ENV=$(APP_ENV))"
	APP_ENV=$(APP_ENV) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d

.PHONY: down
down:
	@echo "▶ Stopping dev stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

.PHONY: clean
clean:
	@echo "▶ Cleaning dev stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans


# --------------------------------------------------
# Run
# --------------------------------------------------
.PHONY: run
run: build up
	@echo "▶ Running: $(ARGS)"
	APP_ENV=$(APP_ENV) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm \
	$(APP_SERVICE) sh -lc "uv run $(ARGS)"

# --------------------------------------------------
# Logs / Shell
# --------------------------------------------------
.PHONY: logs
logs:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f $(APP_SERVICE)

.PHONY: shell
shell:
	APP_ENV=$(APP_ENV) \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) run --rm \
	$(APP_SERVICE) sh

# --------------------------------------------------
# Lint / Test
# --------------------------------------------------
.PHONY: lint
lint:
	$(RUFF) check --fix .
	$(RUFF) format .

.PHONY: test
test:
	$(MAKE) -f Makefile.test $(ARGS)

# --------------------------------------------------
# Make arg passthrough
# --------------------------------------------------
%:
	@:
