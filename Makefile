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
# AWS / LocalStack
# --------------------------------------------------
AWS_REGION ?= ap-south-1
S3_BUCKET ?= fx-ml-data
RAW_FILE_INDEX_TABLE ?= raw_file_index
AWS := aws

ifeq ($(USE_LOCALSTACK),true)
AWS_ENDPOINT := --endpoint-url=http://localhost:4566 --no-sign-request
else
AWS_ENDPOINT :=
AWS_ENV :=
endif

# --------------------------------------------------
# Docker
# --------------------------------------------------
COMPOSE_FILE ?= docker-compose.yml
DOCKER_COMPOSE := docker compose

APP_SERVICE := qf_app
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
	@echo "Infra:"
	@echo "  make infra           Create S3 + DynamoDB (LocalStack)"
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
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d $(DEPS)

.PHONY: down
down:
	@echo "▶ Stopping dev stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

.PHONY: clean
clean:
	@echo "▶ Cleaning dev stack"
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans

# --------------------------------------------------
# LocalStack readiness (Option A – AWS-native)
# --------------------------------------------------
.PHONY: wait-localstack
wait-localstack:
ifeq ($(USE_LOCALSTACK),true)
	@echo "▶ Waiting for LocalStack AWS APIs (S3, DynamoDB)"
	@until \
		$(AWS) s3 ls --endpoint-url=http://localhost:4566 >/dev/null 2>&1 && \
		$(AWS) dynamodb list-tables --endpoint-url=http://localhost:4566 >/dev/null 2>&1; do \
		sleep 2; \
	done
	@echo "✔ LocalStack S3 and DynamoDB are ready"
endif

# --------------------------------------------------
# Infra bootstrap
# --------------------------------------------------
.PHONY: create-s3
create-s3:
ifeq ($(USE_LOCALSTACK),true)
	@echo "▶ Ensuring S3 bucket $(S3_BUCKET) exists"
	@$(AWS) s3api head-bucket --bucket $(S3_BUCKET) $(AWS_ENDPOINT) 2>/dev/null || \
	$(AWS) s3api create-bucket \
		--bucket $(S3_BUCKET) \
		--region $(AWS_REGION) \
		--create-bucket-configuration LocationConstraint=$(AWS_REGION) \
		$(AWS_ENDPOINT)
endif

.PHONY: create-dynamodb
create-dynamodb:
ifeq ($(USE_LOCALSTACK),true)
	@echo "▶ Ensuring DynamoDB table $(RAW_FILE_INDEX_TABLE) exists"
	@$(AWS) dynamodb describe-table \
		--table-name $(RAW_FILE_INDEX_TABLE) \
		>/dev/null 2>&1 || \
	$(AWS) dynamodb create-table \
		--table-name $(RAW_FILE_INDEX_TABLE) \
		--attribute-definitions \
			AttributeName=pk,AttributeType=S \
			AttributeName=sk,AttributeType=S \
		--key-schema \
			AttributeName=pk,KeyType=HASH \
			AttributeName=sk,KeyType=RANGE \
		--billing-mode PAY_PER_REQUEST \
		$(AWS_ENDPOINT)
endif

.PHONY: infra
infra: wait-localstack create-s3 create-dynamodb

# --------------------------------------------------
# Run
# --------------------------------------------------
.PHONY: run
run: build up infra
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
	$(RUFF) check .
	$(RUFF) format --check .

.PHONY: test
test:
	$(MAKE) -f Makefile.test all

# --------------------------------------------------
# Make arg passthrough
# --------------------------------------------------
%:
	@:
