# TEST_README.md — Testing Guide for QF-downloader

This document describes **how tests are structured and executed** in this repository, including:

- Local (developer machine) test execution
- Docker-based integration tests (LocalStack)
- Makefile targets and variables
- Test dependencies and generated artifacts

---

## 1) Overview

This repo uses **pytest** for all tests.

- **Unit tests**: fast, no Docker, use mocks/tmp paths
- **Integration tests**: exercise AWS integrations (S3 + DynamoDB) against **LocalStack**

Coverage reporting is enabled by default via `pytest.ini` and can be augmented via the Makefile.

---

## 2) Test Dependencies (Libraries)

Declared in `pyproject.toml` under dev dependencies.

Core test tooling:

- `pytest`: test runner
- `pytest-cov`: coverage integration and `coverage.xml` generation
- `pytest-mock`: convenience fixtures for mocking

Integration-test related tooling:

- `boto3`: AWS SDK used by integration tests to validate LocalStack connectivity and DynamoDB/S3 behaviors
- `localstack-client`: helper utilities for LocalStack-based environments (dependency only; tests interact primarily via `boto3`)

General dev tooling often used alongside tests:

- `ruff`: formatting and linting

---

## 3) Repository Test Layout

Tests live under the `tests/` directory:

- `tests/unit/`
  - Pure Python tests; should not require network access or Docker.
  - Uses `tmp_path`, mocks (`AsyncMock`), and small deterministic scenarios.

- `tests/integration/`
  - Integration tests that validate interactions with AWS-like services.
  - Designed to run with LocalStack.

Notable files:

- `tests/integration/conftest.py`
  - Defines LocalStack fixtures and environment setup.

---

## 4) Pytest Configuration

Pytest is configured via `pytest.ini`:

- `testpaths = tests`
- Coverage defaults:
  - `addopts = --cov=src --cov-report=xml`
- Custom marker:
  - `docker`: marks tests intended to run with Docker/LocalStack

### 4.1 Markers

Integration tests are marked:

```python
import pytest

@pytest.mark.docker
def test_something_against_localstack(...):
    ...
```

Run only docker-marked tests:

```bash
uv run --dev -- python -m pytest -m docker
```

Exclude docker-marked tests:

```bash
uv run --dev -- python -m pytest -m "not docker"
```

---

## 5) Integration Tests: LocalStack Contract

### 5.1 How LocalStack is detected

`tests/integration/conftest.py` configures a session-scoped fixture that:

- Sets `APP_ENV=localstack`
- Sets `LOCALSTACK_URL` (defaults to `http://localhost:4566` if not provided)
- Provides default AWS creds if none are set:
  - `AWS_ACCESS_KEY_ID=test`
  - `AWS_SECRET_ACCESS_KEY=test`
  - `AWS_REGION=us-east-1`
- Generates **unique** resource names per test session unless pre-set:
  - `S3_BUCKET=qf-test-...`
  - `RAW_FILE_INDEX_TABLE=raw-file-index-...`

It then probes LocalStack (`s3.list_buckets()`). If LocalStack is not reachable, tests will be **skipped** with a message indicating the endpoint.

### 5.2 Services used

The integration suite currently expects at least:

- S3
- DynamoDB

These are started in Docker using the test compose stack.

---

## 6) Running Tests Locally (Recommended)

### 6.1 Prerequisites

- Python version per `pyproject.toml` (currently **>= 3.13**)
- Recommended: `uv`

Install dependencies (dev):

```bash
uv sync --dev
```

If you prefer editable install semantics:

```bash
uv pip install -e ".[dev]"
```

### 6.2 Run unit tests

Most common local command:

```bash
make test SUITE=unit
```

Run the full local check (format-check + lint + tests):

```bash
make check SUITE=unit
```

Equivalent without Makefile:

```bash
uv run --dev -- python -m pytest tests/unit -vv
```

### 6.3 Run all tests locally

```bash
make test SUITE=all
```

---

## 7) Running Integration Tests (Docker + LocalStack)

### 7.1 Prerequisites

- Docker
- Docker Compose v2 (`docker compose ...`)

### 7.2 Run integration suite via Makefile

This is the most reproducible workflow:

```bash
make test SUITE=integration RUNTIME=docker
```

What happens:

- Docker stack is started using `docker-compose.test.yml`
- Integration tests are executed
- Docker stack is brought down after the run

### 7.3 Run integration suite directly via Docker Compose

The repository provides a `docker-compose.test.yml` that runs:

- LocalStack container
- A test runner container built from `Dockerfile.test`

Typical direct commands:

```bash
docker compose -f docker-compose.test.yml up -d --build
# (optional) follow logs
# docker compose -f docker-compose.test.yml logs -f
```

To run tests in the `qf_app` container (compose already defines a pytest command):

```bash
docker compose -f docker-compose.test.yml run --rm qf_app
```

Then teardown:

```bash
docker compose -f docker-compose.test.yml down --remove-orphans --volumes
```

### 7.4 Note on the second compose file

There is also `docker/docker-compose.test.yml`, which is very similar but names the app service `mt5_app`. For consistency, prefer the root `docker-compose.test.yml` unless you specifically need the `docker/` variant.

---

## 8) Makefile Test Targets (How CI/dev runs tests)

The Makefile is the canonical interface for tests.

### 8.1 Common targets

- `make setup`
  - Sync dependencies (tries `uv sync --venv .venv`, then `uv sync --dev`, then `uv sync`)
  - Ensures pytest is available (may fall back to creating `.venv` and installing `.[dev]`)

- `make format`
  - Auto-format code using Ruff (`ruff format .`)

- `make format-check`
  - Verify formatting is clean without making changes (`ruff format --check .`)

- `make lint`
  - Run Ruff lint checks (`ruff check .`)

- `make lint-fix`
  - Auto-fix lint issues where possible (`ruff check . --fix`)

- `make check`
  - Runs `format-check` + `lint` + `test` (respects `SUITE` and `RUNTIME`)

- `make test`
  - Runs tests with variables:
    - `SUITE=unit|integration|all` (default: `all`)
    - `RUNTIME=local|docker` (default: `local`)

- `make coverage`
  - Runs `make test WITH_COVERAGE=true` (adds terminal coverage report + `coverage.xml`)

- `make teardown`
  - Stops dockerized stack (if `RUNTIME=docker`) and removes common artifacts

- `make clean`
  - Removes `.pytest_cache`, `.coverage`, `coverage.xml`, and `.venv`

### 8.2 Useful variables

You can override these on the command line:

- `SUITE`: which suite to run
  - `unit` → `tests/unit`
  - `integration` → `tests/integration`
  - `all` → both
- `RUNTIME`: whether to start Docker dependencies
  - `local` (default)
  - `docker`
- `APP_ENV`: exported to tests (default: `production`)
- `PYTEST_ARGS`: extra args appended to pytest

Examples:

Run a single test file:

```bash
make test SUITE=unit PYTEST_ARGS="-k guess_content_type -vv"
```

Run integration tests with verbose output:

```bash
make test SUITE=integration RUNTIME=docker PYTEST_ARGS="-vv"
```

---

## 9) Test Artifacts (Generated Files)

Common artifacts you may see after running tests:

- `.pytest_cache/`
- `.coverage`
- `coverage.xml`

Cleanup options:

```bash
make clean
# or (docker focused)
make teardown RUNTIME=docker
```

---

## 10) Windows Notes

- The Makefile uses `/bin/sh` and assumes a POSIX-like shell.
- On Windows, the simplest options are:
  - Run via **WSL**, or
  - Use a Git Bash / MSYS2 shell that provides `make` + `/bin/sh`.

If you cannot use `make`, you can always run pytest directly via `uv run` as shown above.

---

## 11) Troubleshooting

### LocalStack tests are skipped

If you run integration tests and see skips like “LocalStack is not reachable…”, ensure:

- LocalStack is running and reachable at `LOCALSTACK_URL` (default `http://localhost:4566`)
- If running inside Docker Compose, `LOCALSTACK_URL` should typically be `http://localstack:4566` (the compose file sets this)

### Confusing coverage configuration

- `pytest.ini` already enables XML coverage reporting.
- The Makefile’s `coverage` target adds additional coverage flags (`--cov-report term-missing`).

If you see duplicated `--cov` flags, prefer running via `make coverage` (single canonical command) or adjust `PYTEST_ARGS` to avoid re-specifying coverage.

---

## 12) What the Tests Currently Cover (High level)

Unit tests:

- `ProviderDownloader` behavior for upload vs skip (checksum dedupe), header/api-key injection, and basic auth
- `DownloadDB` initialization and checksum existence tracking
- Utility helpers like directory creation, content type guessing, and SHA-256 checksums

Integration tests (LocalStack):

- S3 upload + existence check via `qf_downloader.storage.S3Client`
- DynamoDB put/get roundtrip via `qf_downloader.aws_clients.get_boto3_client`
- Index/query contract via `qf_downloader.s3_indexer.S3Indexer`
