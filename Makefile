SHELL := /bin/sh
.DEFAULT_GOAL := help

UV ?= uv
# Use `uv run --dev -- python -m pytest` so pytest runs under the synced venv.
# This uses the `--dev` context which is supported by local `uv` versions.
PYTEST ?= $(UV) run --dev -- python -m pytest
RUFF ?= $(UV) run --dev -- ruff
APP_ENV ?= production
SUITE ?= all
RUNTIME ?= local
WITH_COVERAGE ?= false
DOCKER_COMPOSE_FILE ?= docker-compose.test.yml
COVERAGE_PACKAGE ?= qf_downloader
UNIT_TEST_PATH ?= tests/unit
INTEGRATION_TEST_PATH ?= tests/integration
VENV ?= .venv
PYTEST_ARGS ?=

DOCKER_COMPOSE := docker compose -f $(DOCKER_COMPOSE_FILE)

.PHONY: help setup format format-check lint lint-fix check docker-up docker-down test coverage teardown clean _runtime-up _runtime-down _exec-tests

help:
	@echo "Available targets:"
	@echo "  make setup                # Sync Python dependencies with uv"
	@echo "  make format               # Auto-format code (Ruff)"
	@echo "  make format-check         # Check formatting without changes (Ruff)"
	@echo "  make lint                 # Run lint checks (Ruff)"
	@echo "  make lint-fix             # Auto-fix lint issues where possible (Ruff)"
	@echo "  make check                # Run format-check + lint + tests (respects SUITE/RUNTIME)"
	@echo "  make test                 # Run parametrized test suite (SUITE=unit|integration|all, RUNTIME=local|docker)"
	@echo "  make coverage             # Run tests with coverage reporting"
	@echo "  make teardown             # Stop dockerized test stack and clean artifacts"
	@echo "  make clean                # Remove caches and coverage data"

format:
	@echo "[ruff] formatting";
	$(RUFF) format .

format-check:
	@echo "[ruff] format check";
	$(RUFF) format --check .

lint:
	@echo "[ruff] lint";
	$(RUFF) check .

lint-fix:
	@echo "[ruff] lint (fix)";
	$(RUFF) check . --fix

check:
	@STATUS=0; \
	$(MAKE) --no-print-directory format-check || STATUS=$$?; \
	if [ $$STATUS -eq 0 ]; then $(MAKE) --no-print-directory lint || STATUS=$$?; fi; \
	if [ $$STATUS -eq 0 ]; then $(MAKE) --no-print-directory test SUITE=$(SUITE) RUNTIME=$(RUNTIME) || STATUS=$$?; fi; \
	exit $$STATUS

setup:
	@echo "[setup] Ensuring Python deps are synced via $(UV)"
	@set -e; \
	# Try the modern --venv flag first, fall back to --dev, then to plain sync
	if $(UV) sync --venv $(VENV) >/dev/null 2>&1; then \
		echo "[setup] using $(UV) sync --venv $(VENV)"; \
		$(UV) sync --venv $(VENV); \
	elif $(UV) sync --dev >/dev/null 2>&1; then \
		echo "[setup] falling back to $(UV) sync --dev"; \
		$(UV) sync --dev; \
	else \
		echo "[setup] falling back to $(UV) sync"; \
		$(UV) sync; \
	fi
	# Ensure pytest is installable / available in the venv. If missing, create venv and
	# install dev extras from pyproject.toml
	if [ -x "$(VENV)/bin/python" ] && "$(VENV)/bin/python" -c 'import pytest' >/dev/null 2>&1; then \
		echo "[setup] pytest available in $(VENV) (bin)"; \
	elif [ -x "$(VENV)/Scripts/python" ] && "$(VENV)/Scripts/python" -c 'import pytest' >/dev/null 2>&1; then \
		echo "[setup] pytest available in $(VENV) (Scripts)"; \
	else \
		echo "[setup] pytest not found in venv; creating venv and installing dev deps"; \
		if [ ! -x "$(VENV)/bin/python" ] && [ ! -x "$(VENV)/Scripts/python" ]; then \
			python -m venv $(VENV) --upgrade-deps; \
		fi; \
		if [ -x "$(VENV)/bin/python" ]; then PYV="$(VENV)/bin/python"; else PYV="$(VENV)/Scripts/python"; fi; \
		"$${PYV}" -m ensurepip --upgrade >/dev/null 2>&1 || true; \
		"$${PYV}" -m pip install --upgrade pip setuptools >/dev/null; \
		"$${PYV}" -m pip install -e '.[dev]'; \
	fi

_runtime-up:
	@if [ "$(RUNTIME)" = "docker" ]; then \
		echo "[runtime] Starting dockerized test deps via $(DOCKER_COMPOSE_FILE)"; \
		$(DOCKER_COMPOSE) up -d --build; \
	fi

_runtime-down:
	@if [ "$(RUNTIME)" = "docker" ]; then \
		echo "[runtime] Stopping dockerized test deps"; \
		$(DOCKER_COMPOSE) down --remove-orphans --volumes; \
	fi

_exec-tests:
	@set -euo pipefail; \
	if [ "$(SUITE)" = "unit" ]; then \
		TARGETS="$(UNIT_TEST_PATH)"; \
	elif [ "$(SUITE)" = "integration" ]; then \
		TARGETS="$(INTEGRATION_TEST_PATH)"; \
	else \
		TARGETS="$(UNIT_TEST_PATH) $(INTEGRATION_TEST_PATH)"; \
	fi; \
	CMD="$(PYTEST) $$TARGETS $(PYTEST_ARGS)"; \
	if [ "$(WITH_COVERAGE)" = "true" ]; then \
		CMD="$$CMD --cov $(COVERAGE_PACKAGE) --cov-report term-missing --cov-report=xml"; \
	fi; \
	echo "[pytest] APP_ENV=$(APP_ENV) $$CMD"; \
	APP_ENV=$(APP_ENV) $$CMD

test:
	@STATUS=0; \
	$(MAKE) --no-print-directory setup || STATUS=$$?; \
	if [ $$STATUS -eq 0 ]; then $(MAKE) --no-print-directory _runtime-up || STATUS=$$?; fi; \
	if [ $$STATUS -eq 0 ]; then $(MAKE) --no-print-directory _exec-tests || STATUS=$$?; fi; \
	RUNTIME=$(RUNTIME) $(MAKE) --no-print-directory _runtime-down; \
	exit $$STATUS

coverage:
	@$(MAKE) --no-print-directory test WITH_COVERAGE=true

teardown:
	@RUNTIME=$(RUNTIME) $(MAKE) --no-print-directory _runtime-down
	@rm -rf .pytest_cache .coverage coverage.xml

clean:
	@rm -rf .pytest_cache .coverage coverage.xml $(VENV)

docker-up:
	@RUNTIME=docker $(MAKE) --no-print-directory _runtime-up

docker-down:
	@RUNTIME=docker $(MAKE) --no-print-directory _runtime-down
