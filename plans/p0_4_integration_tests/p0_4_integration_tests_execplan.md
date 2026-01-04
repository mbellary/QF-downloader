# P0.4 — Integration Tests (LocalStack + Docker) for QF-downloader

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, the repository will have integration tests that validate the real service boundaries of the downloader pipeline using a fully local environment:

- Local AWS emulation via LocalStack (S3 + DynamoDB)
- Optional Docker execution of the tests themselves
- Makefile-driven orchestration so developers and CI run the same commands

The observable outcome is that a contributor can run integration tests either:

- locally (pytest on host, LocalStack in Docker), or
- fully in Docker (pytest in a container, LocalStack in a container)

…and see a real S3 object created and a real DynamoDB index entry created using the repository’s production clients (`S3Client` and `S3Indexer`).

This plan is scoped to integration behavior. Unit tests and offline behavior are explicitly handled in `plans/p0_4_unit_tests/p0_4_unit_tests_execplan.md`.

## Progress

- [x] (2026-01-04 00:00Z) Verified the repository already includes Docker test scaffolding: `Dockerfile.test`, `docker-compose.test.yml`, and `docker/docker-compose.test.yml`.
- [x] (2026-01-04 00:00Z) Verified local Makefile supports starting Dockerized dependencies via `RUNTIME=docker`.
- [x] (2026-01-04 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/QF-downloader/issues/6
- [x] (2026-01-04 00:00Z) Created design document: `plans/p0_4_integration_tests/p0_4_integration_tests_design.md`
- [x] (2026-01-04 00:00Z) Implemented LocalStack-backed integration tests: `tests/integration/test_localstack_boundaries.py` with fixtures in `tests/integration/conftest.py`.
- [ ] Define a minimal but real integration scenario: write to S3 and index to DynamoDB using LocalStack, then query back (S3 implemented; DynamoDB roundtrip implemented; S3Indexer path pending fix).
- [ ] Update Docker Compose configuration so LocalStack provides the services the code uses (S3 and DynamoDB) and so container-to-container networking works.
- [ ] Update CI to run integration tests in Docker consistently with local workflows.

## Surprises & Discoveries

- Observation: The root `docker-compose.test.yml` and `docker/docker-compose.test.yml` are nearly duplicates.
  Evidence: Both define `mt5_app` + `localstack`, with the same test command.

- Observation: LocalStack is currently configured for S3 only, but production code indexes to DynamoDB.
  Evidence: `src/qf_downloader/s3_indexer.py` uses a DynamoDB client, while `docker-compose.test.yml` sets `SERVICES: s3`.

- Observation: LocalStack endpoint URL is currently `http://localhost:4566` in `src/qf_downloader/.env.dev`, which is not correct for container-to-container networking.
  Evidence: In Docker Compose, `mt5_app` must reach LocalStack via service DNS name (typically `http://localstack:4566`).

- Observation: Existing CI workflow includes a Docker integration job, but it refers to `docker/docker-compose.test.yml` and other stale project names.
  Evidence: `.github/workflows/full_pipeline.yml` uses `greetings_lib` coverage settings and runs Docker Compose from `docker/docker-compose.test.yml`.

## Decision Log

- Decision: Integration tests will cover S3 + DynamoDB using LocalStack and will validate both write and read paths.
  Rationale: These are the core “remote” dependencies in the downloader pipeline; proving them in LocalStack provides high confidence without hitting real AWS.
  Date/Author: 2026-01-04 / Copilot

- Decision: Prefer a single source of truth for the Docker test stack (one Compose file) and make Makefile/CI call it.
  Rationale: Duplicate compose files drift quickly and cause “works in CI but not locally” failures.
  Date/Author: 2026-01-04 / Copilot

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps implementation coordination tied to the living plan without duplicating status across multiple places.
  Date/Author: 2026-01-04 / Copilot (Issue: https://github.com/mbellary/QF-downloader/issues/6)

## Outcomes & Retrospective

Not started.

## Context and Orientation

The production integration surface that must be validated is:

- `src/qf_downloader/storage.py:S3Client` uses `aioboto3` and switches behavior on `APP_ENV`.
  - When `APP_ENV == "localstack"`, it uses `LOCALSTACK_URL` and explicit credentials.
  - Otherwise it attempts to use IAM-role / profile behavior.

- `src/qf_downloader/s3_indexer.py:S3Indexer` writes an item into DynamoDB table `RAW_FILE_INDEX_TABLE` using `get_aboto3_client("dynamodb")` from `src/qf_downloader/aws_clients.py`.

- `src/qf_downloader/downloader.py:ProviderDownloader` glues together fetch + checksum ledger (`src/qf_downloader/db.py:DownloadDB`) + S3 upload + DynamoDB index.

Existing test infrastructure:

- `Dockerfile.test` installs the project with dev extras and defaults to `pytest`.
- `docker-compose.test.yml` (repo root) builds `mt5_app` and starts `localstack`.
- `docker/docker-compose.test.yml` is similar but uses `context: ..`.
- `pytest.ini` defines a `docker` marker and auto-enables `--cov=src --cov-report=xml`.

## Plan of Work

This plan adds real integration tests and ensures they can be executed locally and in Docker.

Implementation must follow the design in `plans/p0_4_integration_tests/p0_4_integration_tests_design.md`.

1) Choose and document the integration contract

Define “integration test” as:

- Uses LocalStack for AWS dependencies.
- May use real SQLite on disk via `tmp_path`.
- Must not depend on external internet.

2) Make LocalStack match the production dependencies

Update the test Docker Compose stack so LocalStack runs the required services:

- Enable `s3` and `dynamodb` in LocalStack.
- Provide stable networking from the test runner to LocalStack by setting:
  - `APP_ENV=localstack`
  - `LOCALSTACK_URL=http://localstack:4566` (inside Docker) or `http://localhost:4566` (when running pytest on the host)

3) Add deterministic LocalStack setup/teardown

Add a small helper (preferably a pytest fixture) that:

- Creates the S3 bucket from `S3_BUCKET`.
- Creates the DynamoDB table named by `RAW_FILE_INDEX_TABLE`.

The DynamoDB schema must match what `S3Indexer` expects:

- Partition key `pk` (string)
- Sort key `sk` (string)

4) Implement a minimal “real boundary” integration test suite

Replace `tests/integration/test_dummy_integration.py` with tests that validate:

- S3 write path:
  - Use `S3Client.upload_file(...)` to write a known payload.
  - Use either `S3Client.object_exists(...)` or a boto3 `head_object` to verify the object exists.

- DynamoDB write + query path:
  - Use `S3Indexer.index_file(...)` to create an item.
  - Use `S3Indexer.query_keys(...)` to read back the key within a date range.

- Optional end-to-end “download_and_upload without real HTTP”:
  - Instantiate `ProviderDownloader` with a provider definition.
  - Patch `_fetch()` to return deterministic bytes.
  - Use a real `DownloadDB` pointing at a `tmp_path` db.
  - Assert that calling `_download_single_day(...)` results in:
    - an object in S3,
    - an entry in DynamoDB,
    - an entry in the SQLite ledger.

This “optional” E2E test provides the best confidence while still keeping HTTP fully offline.

5) Makefile and CI wiring

Align local and CI invocations so they use the same entrypoints:

- Local host-mode integration:
  - Start LocalStack with Docker.
  - Run pytest on the host.

- Docker-mode integration:
  - Run pytest in the `mt5_app` container.

Update Makefile targets so a contributor can do:

- `make test SUITE=integration RUNTIME=docker` (host pytest, dockerized deps)
- `make docker-up` / `make docker-down` as needed
- Add a dedicated target (if required) that runs tests inside Docker Compose, matching CI.

Update `.github/workflows/full_pipeline.yml` so CI runs:

- Ruff format check
- Ruff lint
- Unit tests
- Docker integration tests (compose up, abort on test container exit)

## Concrete Steps

All commands should be run from the repository root.

Before implementing, read `plans/p0_4_integration_tests/p0_4_integration_tests_design.md` and keep this ExecPlan consistent with any design decisions recorded there.

1) Environment setup

    uv pip install -e ".[dev]"

2) Local integration (pytest on host, LocalStack in Docker)

    make docker-up
    APP_ENV=localstack LOCALSTACK_URL=http://localhost:4566 make test SUITE=integration RUNTIME=local
    make docker-down

3) Docker integration (pytest in container)

If the chosen Compose file defines a test-runner service (for example `mt5_app`), run:

    docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

Expected behavior (example):

    ... localstack started ...
    ... pytest collected N integration tests ...
    N passed ...
    Coverage XML written to file coverage.xml

4) Cleanup

    make teardown RUNTIME=docker

## Validation and Acceptance

Acceptance is met when all of the following are true:

- Integration tests under `tests/integration/` validate real S3 + DynamoDB behavior against LocalStack.
- Integration tests pass in both execution modes:
  - host pytest with Dockerized LocalStack, and
  - pytest-in-Docker via Docker Compose.
- Makefile provides a stable, documented one-command path to run integration tests.
- CI runs integration tests using the same compose workflow that developers use locally.

The integration test suite that must pass includes at least:

- `tests/integration/conftest.py`
- `tests/integration/test_localstack_boundaries.py`

Note: `tests/integration/test_localstack_boundaries.py::test_s3indexer_index_and_query` is currently marked `xfail` because `src/qf_downloader/s3_indexer.py` treats an `aioboto3` client as a resource (`Table()`), which is incompatible. Once corrected, this test should be changed to a normal passing test.

Note: In Tester mode, tests are implemented but not executed by this agent. Execution validation is expected to be performed by the Developer.

## Idempotence and Recovery

- LocalStack resources (bucket/table) should be created idempotently by the test fixture.
- The integration suite must not depend on existing state; it should create/clean unique keys per test run.
- If containers are left running after a failure, `make teardown RUNTIME=docker` should stop and remove them.

## Artifacts and Notes

Current Docker entrypoints (pre-change) for reference:

- `docker-compose.test.yml` runs `pytest tests/integration -m docker -vv` in the container.
- LocalStack currently only enables S3; DynamoDB must be added for `S3Indexer` coverage.

## Interfaces and Dependencies

Existing dependencies to leverage:

- LocalStack (Docker image) for AWS emulation.
- `boto3` (already in dev deps) for setup assertions and resource provisioning.

No additional integration-test libraries are required; use plain pytest + boto3/aioboto3.
