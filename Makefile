SHELL := /bin/sh
.DEFAULT_GOAL := help

# --------------------------------------------------
# Config
# --------------------------------------------------
APP_NAME        := qf-downloader
DEV_IMAGE       := $(APP_NAME):dev
PROD_IMAGE      := $(APP_NAME):prod

DOCKERFILE_DEV  := Dockerfile.dev
DOCKERFILE_PROD := Dockerfile.prod

COMPOSE_DEV     := docker-compose.yml
COMPOSE_TEST    := docker-compose.test.yml

UV              ?= uv
PYTHON          := $(UV) run --dev -- python
RUFF            := $(UV) run --dev -- ruff

# --------------------------------------------------
# Help
# --------------------------------------------------
.PHONY: help
help:
	@echo ""
	@echo "Development targets:"
	@echo "  build-dev        Build dev Docker image"
	@echo "  build-prod       Build prod Docker image"
	@echo "  run              Run dev stack (docker-compose)"
	@echo "  stop             Stop dev stack"
	@echo "  logs             Tail dev logs"
	@echo ""
	@echo "Quality:"
	@echo "  lint             Run ruff lint + format check"
	@echo "  test             Run all tests (delegates to Makefile.test)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean            Remove containers, images, cache"
	@echo ""

# --------------------------------------------------
# Build
# --------------------------------------------------
.PHONY: build-dev
build-dev:
	docker build -f $(DOCKERFILE_DEV) -t $(DEV_IMAGE) .

.PHONY: build-prod
build-prod:
	docker build -f $(DOCKERFILE_PROD) -t $(PROD_IMAGE) .

# --------------------------------------------------
# Run (Development)
# --------------------------------------------------
.PHONY: run
run:
	docker compose -f $(COMPOSE_DEV) up --build

.PHONY: stop
stop:
	docker compose -f $(COMPOSE_DEV) down

.PHONY: logs
logs:
	docker compose -f $(COMPOSE_DEV) logs -f

# --------------------------------------------------
# Lint (local dev, fast feedback)
# --------------------------------------------------
.PHONY: lint
lint:
	$(RUFF) check .
	$(RUFF) format --check .

# --------------------------------------------------
# Tests (delegate to existing Makefile)
# --------------------------------------------------
.PHONY: test
test:
	$(MAKE) -f Makefile.test all

# --------------------------------------------------
# Cleanup
# --------------------------------------------------
.PHONY: clean
clean:
	docker compose -f $(COMPOSE_DEV) down -v --remove-orphans
	docker image rm -f $(DEV_IMAGE) $(PROD_IMAGE) 2>/dev/null || true
	rm -rf .ruff_cache .pytest_cache __pycache__
