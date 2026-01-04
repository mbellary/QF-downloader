# Inventory for the feature

This design document covers the feature plan in `plans/p0_4_integration_tests/p0_4_integration_tests_execplan.md` and must be kept consistent with that ExecPlan.

## Components and modules affected

### `tests/integration/` (new + updates)

**Current functionality:**

- `tests/integration/test_dummy_integration.py` exists as a placeholder and only asserts `True`.

**Impact from this feature:**

- Replace placeholder integration tests with LocalStack-backed tests that validate real S3 + DynamoDB boundaries.
- Tests must be runnable in two modes:
  - host pytest with Dockerized LocalStack
  - pytest inside a container via Docker Compose

### `docker-compose.test.yml` (root) and `docker/docker-compose.test.yml`

**Current functionality:**

- Both define `mt5_app` (pytest runner container) and `localstack`.
- LocalStack only enables `SERVICES: s3`.

**Impact from this feature:**

- Ensure LocalStack provides **both** `s3` and `dynamodb` because production code uses both.
- Normalize to one Compose file as the single source of truth to avoid drift.
- Ensure correct endpoint networking:
  - host mode: LocalStack reachable at `http://localhost:4566`
  - container mode: LocalStack reachable at `http://localstack:4566`

### `Dockerfile.test`

**Current functionality:**

- Builds a test runner image and installs the package with dev extras.
- Default CMD runs `pytest`.

**Impact from this feature:**

- Ensure the container has all tools needed for integration setup (pytest, boto3, awscli-local optional).
- Ensure the runner can create buckets/tables via boto3 (or awscli-local) against LocalStack.

### `src/qf_downloader/storage.py:S3Client`

**Current functionality:**

- When `APP_ENV == "localstack"`, uses `LOCALSTACK_URL` as endpoint.

**Impact from this feature:**

- Integration tests will exercise this behavior directly.
- The test stack must set `APP_ENV=localstack` and an appropriate `LOCALSTACK_URL`.

### `src/qf_downloader/s3_indexer.py:S3Indexer` and `src/qf_downloader/aws_clients.py`

**Current functionality:**

- `S3Indexer` writes to DynamoDB table `RAW_FILE_INDEX_TABLE`.

**Impact from this feature:**

- Integration tests must provision a DynamoDB table with `pk` and `sk` keys.
- The LocalStack test stack must enable DynamoDB.

### `src/qf_downloader/downloader.py:ProviderDownloader` and `src/qf_downloader/db.py:DownloadDB`

**Current functionality:**

- Orchestrates fetch → dedupe → upload → index.

**Impact from this feature:**

- Optional “end-to-end but offline HTTP” integration test may cover this flow with `_fetch()` patched to deterministic bytes.

### `Makefile`

**Current functionality:**

- Supports `make test SUITE=integration` and can start/stop dockerized deps with `RUNTIME=docker`.

**Impact from this feature:**

- Add or refine targets (during implementation) so developers can run integration tests consistently.
- Ensure Makefile targets align with CI jobs.

### `.github/workflows/full_pipeline.yml`

**Current functionality:**

- Contains lint/test jobs but includes stale references (e.g., `greetings_lib`, compose path in `docker/docker-compose.test.yml`).

**Impact from this feature:**

- Update CI to run integration tests through the chosen, single Compose stack and to use correct coverage target/package.

---

# Design for the feature

## Goals and non-goals

**Goals**

- Provide integration tests that validate the repo’s production AWS boundary clients against LocalStack:
  - S3: put object + head object
  - DynamoDB: put item + query item(s)
- Support two execution modes:
  - Host pytest + Dockerized LocalStack
  - Docker Compose where pytest runs in a container
- Make it deterministic and self-contained: tests create required resources (bucket/table) and use unique keys.

**Non-goals**

- Do not hit real AWS.
- Do not depend on internet.
- Do not test provider HTTP downloads from external sources (patch `_fetch` for deterministic payloads).

## Execution modes

### Mode A: Host pytest + Dockerized LocalStack

- Start LocalStack via Docker Compose.
- Run `pytest tests/integration` on host.
- Use `LOCALSTACK_URL=http://localhost:4566`.

This is the fastest iteration loop for developers.

### Mode B: Full Docker Compose

- Run `pytest` inside `mt5_app` container.
- LocalStack runs as a sibling container.
- Use `LOCALSTACK_URL=http://localstack:4566`.

This matches CI most closely.

## LocalStack service design

LocalStack must enable at least:

- `s3`
- `dynamodb`

Also, the test stack should expose the edge port 4566.

Recommended environment for LocalStack container:

- `SERVICES=s3,dynamodb`
- `DEFAULT_REGION=us-east-1`

## Integration test resource provisioning

Integration tests require creating:

1) An S3 bucket named by `S3_BUCKET`
2) A DynamoDB table named by `RAW_FILE_INDEX_TABLE` with keys:

- Partition key: `pk` (string)
- Sort key: `sk` (string)

Design for provisioning:

- Use a pytest fixture in `tests/integration/conftest.py`.
- Provision resources via boto3 against LocalStack endpoint.
- Make creation idempotent:
  - bucket create should ignore “already exists” style errors in LocalStack
  - table create should ignore “ResourceInUseException”

## Test cases

### Test 1: S3 boundary via `S3Client`

- Arrange:
  - `APP_ENV=localstack`
  - `LOCALSTACK_URL` endpoint
  - credentials (LocalStack accepts dummy)
  - `S3_BUCKET` set
- Act: `await S3Client.upload_file(content=b"hello", key="test/key.bin")`
- Assert: `await S3Client.object_exists(key)` is True

### Test 2: DynamoDB boundary via `S3Indexer`

- Arrange:
  - `RAW_FILE_INDEX_TABLE` created
- Act: `await S3Indexer.index_file(provider, pair, date, s3_key)`
- Assert: `await S3Indexer.query_keys(...)` returns expected s3_key within range

### Test 3 (optional): End-to-end downloader boundary

- Arrange:
  - Provider config with `save_path` and `url_template`
  - Real `DownloadDB` pointing at temp db path
  - Real `S3Client` (LocalStack)
  - Real `S3Indexer` (LocalStack)
  - Patch `ProviderDownloader._fetch` to return deterministic bytes

- Act: call `_download_single_day(pair, day)`

- Assert:
  - object exists in S3
  - DynamoDB contains indexed key
  - SQLite ledger records the checksum

This is “integration” because it crosses multiple modules and uses LocalStack, but remains offline and deterministic.

## Makefile and CI alignment

Design requirements:

- `make test SUITE=integration RUNTIME=docker` should start LocalStack and run integration tests in a way that works cross-platform.
- CI should use Docker Compose with `--abort-on-container-exit` to fail fast and produce logs.
- The Compose file used in CI must match the Compose file referenced in the Makefile.

## Diagrams

### Integration test topology

Mode A (host pytest):

    pytest (host)  --->  LocalStack (docker)  [s3,dynamodb]  <--  edge 4566

Mode B (docker pytest):

    mt5_app (docker)  --->  localstack (docker)  [s3,dynamodb]
           |                         |
           +-- mounts repo           +-- exposes 4566

### Provisioning flow

    (pytest session)
        |
        +--> create S3 bucket
        |
        +--> create DynamoDB table (pk/sk)
        |
        +--> run tests

## Design compliance notes

- Follow environment management via `uv` and the repo’s Makefile targets (see `AGENTS_ENVIRONMENT.md` and `Makefile`).
- Formatting/linting via `uv run ruff format .` and `uv run ruff check .`.
- Tests must be deterministic and avoid external internet.
