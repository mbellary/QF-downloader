# P0.4 — Unit Test Suite for QF-downloader

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, the repository will have a real unit-test suite that validates the core logic of the downloader without relying on external services (no live HTTP, no AWS, no LocalStack). The observable outcome is that a contributor can run `make test SUITE=unit RUNTIME=local` and see deterministic tests pass quickly while still producing `coverage.xml` for CI.

This plan intentionally treats “unit tests” as tests that isolate a single module or a small group of functions using fakes/mocks and local temp files. Integration tests (LocalStack, Docker, end-to-end flows) are explicitly out of scope for this unit-test plan and are covered in `plans/p0_4_integration_tests/p0_4_integration_tests_execplan.md`.

## Progress

- [x] (2026-01-04 00:00Z) Verified we are on a non-main feature branch: `task/p0_4_fix_ci_python`.
- [x] (2026-01-04 00:00Z) Bootstrapped local dev environment with `uv pip install -e ".[dev]"`.
- [x] (2026-01-04 00:00Z) Ran environment verification commands successfully: `uv run ruff format .`, `uv run ruff check .`, `uv run pytest -vv` (4 tests passed; `coverage.xml` generated).
- [x] (2026-01-04 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/QF-downloader/issues/7
- [x] (2026-01-04 00:00Z) Created design document: `plans/p0_4_unit_tests/p0_4_unit_tests_design.md`
- [ ] Replace the current placeholder unit tests under `tests/unit/` with unit tests that cover real behavior in `src/qf_downloader/`.
- [ ] Ensure unit tests run without Docker and without network access (no HTTP calls, no LocalStack, no AWS).
- [ ] Update documentation references that still mention other packages (math-lib / greetings-lib) so the unit test workflow is unambiguous.

## Surprises & Discoveries

- Observation: The repository already has a pytest layout and a Makefile-driven test runner, but the tests are placeholders.
  Evidence: `tests/unit/test_dummy_ci.py` and `tests/integration/test_dummy_integration.py` only assert `True`.

- Observation: `pytest.ini` already enforces coverage XML generation for CI.
  Evidence: `pytest.ini` sets `addopts = --cov=src --cov-report=xml`.

- Observation: Several “agent” docs appear copy-pasted and reference unrelated package names and paths.
  Evidence: `tests/AGENTS_TESTS.md` references `math_lib`; `src/qf_downloader/AGENTS_CODING_GUIDELINES.md` references `src/greetings_lib/`; `.github/workflows/full_pipeline.yml` references `greetings_lib`.

- Observation: The async helper `file_checksum()` uses `aiofiles`, but `aiofiles` is not listed as a dependency.
  Evidence: `src/qf_downloader/utils.py` imports `aiofiles`, but `pyproject.toml` does not include it.

## Decision Log

- Decision: Avoid adding `pytest-asyncio` for now and keep unit tests runnable using `asyncio.run(...)`.
  Rationale: Minimizes new dependencies and keeps unit tests straightforward; this repo’s current dev extras already include `pytest-mock` but not an asyncio plugin.
  Date/Author: 2026-01-04 / Copilot

- Decision: Treat unit tests as “offline and deterministic”: local filesystem, SQLite temp DB, and pure mocks/fakes for HTTP and AWS clients.
  Rationale: Fast feedback loop and reliable CI; external systems belong in integration tests.
  Date/Author: 2026-01-04 / Copilot

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps implementation coordination tied to the living plan without duplicating status across multiple places.
  Date/Author: 2026-01-04 / Copilot (Issue: https://github.com/mbellary/QF-downloader/issues/7)

## Outcomes & Retrospective

Not started.

## Context and Orientation

Relevant production code is under `src/qf_downloader/`:

- `src/qf_downloader/utils.py`: small pure helpers such as `ensure_dir()` and `guess_content_type()`, plus `file_checksum()` (async file hashing).
- `src/qf_downloader/db.py`: `DownloadDB` (async SQLite checksum ledger) and `Database` (sync SQLite helper).
- `src/qf_downloader/downloader.py`: `ProviderDownloader`, which performs fetch → checksum → dedupe → upload → index.
- `src/qf_downloader/storage.py`: `S3Client` (async S3 put/head with optional LocalStack endpoint) and `LocalStorage` (sync local disk storage).
- `src/qf_downloader/cli.py`: Typer app `app` (runtime CLI) plus a minimal `click.Command` named `cli` used only to satisfy an existing test.

Existing tests live under `tests/`:

- `tests/unit/` currently contains placeholders.
- `tests/test_smoke_import.py` verifies importability.
- `tests/test_cli_help.py` currently uses `click.testing.CliRunner` against `qf_downloader.cli:cli`.

The Makefile already supports running unit tests locally:

- `make test SUITE=unit RUNTIME=local`

## Plan of Work

This plan replaces placeholder unit tests with tests that cover real behavior and edge cases in a way that is stable across OSes (Windows/macOS/Linux).

Implementation must follow the design in `plans/p0_4_unit_tests/p0_4_unit_tests_design.md`.

First, establish clear unit-test boundaries:

- Unit tests must not depend on Docker.
- Unit tests must not depend on LocalStack or AWS.
- Unit tests must not do real HTTP; they must fake `ProviderDownloader._fetch()` or fake `aiohttp.ClientSession.request()`.

Then implement unit tests in a minimal, modular way:

1) Utilities (`src/qf_downloader/utils.py`)

Create a new test file `tests/unit/test_utils.py` with tests for:

- `ensure_dir(path)` creates the directory tree idempotently.
- `guess_content_type(url, filename)` returns:
  - a mimetypes-derived type when a recognized filename extension is provided,
  - an extension-derived fallback for `.csv`, `.pdf`, `.html` / `.htm`,
  - `application/octet-stream` otherwise.

If `file_checksum()` is currently unused, decide whether to test it as-is or treat it as a “dependency hygiene” item. If testing it, either:

- add `aiofiles` to `pyproject.toml` dev/runtime dependencies and test that checksum matches known content, or
- rewrite `file_checksum()` to avoid `aiofiles` (but that becomes production code work).

Because this is a unit-test ExecPlan, the preferred path is: add the missing dependency and then test `file_checksum()`.

2) SQLite ledger (`src/qf_downloader/db.py`)

Create `tests/unit/test_db_download_db.py` that uses `tmp_path` to create a fresh DB file per test.

Use `asyncio.run(...)` to run async methods. Validate:

- `DownloadDB.init()` creates the required tables.
- `exists_checksum(provider, checksum)` is `False` before insert.
- `add_download(...)` inserts a row and updates `fetch_status` for the provider.
- `get_last_successful(provider)` returns `None` before any insert and returns a timestamp after insert.

Also add a small test file `tests/unit/test_db_database_sync.py` (optional) for the `Database` helper:

- `create_tables()` idempotency.
- `insert_download()` + `get_downloads()` returns expected structure.

3) Downloader behavior (`src/qf_downloader/downloader.py`)

Create `tests/unit/test_provider_downloader.py` that tests behavior without network and without AWS by supplying fakes:

- Provide a fake `DownloadDB` object with async methods (`exists_checksum`, `add_download`) implemented using `unittest.mock.AsyncMock`.
- Provide a fake `S3Client` with an async `upload_file()` method implemented via `AsyncMock`.
- Patch `ProviderDownloader.indexer` to a fake with async `index_file()`.
- Patch `ProviderDownloader._fetch()` to return deterministic bytes (and a minimal response-like object).

Validate:

- When the checksum is new, `_download_single_day()` returns status `uploaded` and calls:
  - `s3.upload_file(content=..., key=..., content_type=...)` with a key that matches `save_path` + filename.
  - `db.add_download(provider_key, url, checksum, s3_key)`.
  - `indexer.index_file(provider, pair, date, s3_key)`.

- When the checksum already exists, `_download_single_day()` returns status `skipped` and does not call upload/index.

- `_prepare_headers()` injects an API key only when the provider auth config is `header_api_key` and the env var is present.

- `_prepare_auth()` returns an `aiohttp.BasicAuth` only when `basic` auth env vars are present.

4) CLI expectations (`src/qf_downloader/cli.py`)

Decide whether to keep the minimal `click.Command` (`cli`) as a backwards-compat shim or replace `tests/test_cli_help.py` with a Typer-driven help test.

Preferred unit-test direction:

- Add `tests/unit/test_cli_help.py` that uses Typer’s test runner to exercise `qf_downloader.cli:app --help` and ensure help text includes expected commands (`list-providers`, `run`, `backfill`).
- Remove or demote the old `click.Command` shim only after tests cover the Typer entrypoint.

Because the repo already has a test depending on `cli`, this change must be planned carefully to avoid breaking existing CI.

5) Documentation and consistency cleanup (test-only scope)

Update the testing docs so the unit-test workflow is accurate for this repo:

- `tests/AGENTS_TESTS.md` should reference `qf_downloader` (not `math_lib`) and the real coverage config (`pytest.ini`).
- `src/qf_downloader/AGENTS_CODING_GUIDELINES.md` should reference `src/qf_downloader/` (not `src/greetings_lib/`).

These documentation updates are necessary for new contributors (and future agents) to execute unit tests correctly.

## Concrete Steps

All commands should be run from the repository root.

Before implementing, read `plans/p0_4_unit_tests/p0_4_unit_tests_design.md` and keep this ExecPlan consistent with any design decisions recorded there.

1) Environment setup (idempotent)

    uv --version
    uv pip install -e ".[dev]"

2) Format and lint (must be clean before tests)

    uv run ruff format .
    uv run ruff check .

3) Unit tests only

    make test SUITE=unit RUNTIME=local

Expected output (example):

    collected N items
    ...
    N passed in <time>
    Coverage XML written to file coverage.xml

4) Quick direct invocation (debugging)

    uv run pytest -q tests/unit

## Validation and Acceptance

Acceptance is met when all of the following are true:

- `make test SUITE=unit RUNTIME=local` passes on a clean checkout.
- Unit tests do not make real network calls and do not require Docker.
- Coverage output `coverage.xml` is produced (either via `pytest.ini` defaults or explicit flags) and includes `src/qf_downloader/` modules.
- Placeholder tests under `tests/unit/` are removed or replaced with behavior-validating tests.

## Idempotence and Recovery

This plan is designed to be safe to re-run:

- `uv pip install -e ".[dev]"` is idempotent.
- Unit tests should use `tmp_path` for all filesystem writes and should not depend on persistent state.
- If a test fails due to an import-time `.env` load in `src/qf_downloader/config.py`, use `monkeypatch` + `importlib.reload` within the test to control env deterministically.

## Artifacts and Notes

Current baseline (before unit test improvements) for reference:

- `uv run pytest -vv` currently reports 4 passing tests, but two of them are placeholders.
- `pytest.ini` already writes `coverage.xml`.

## Interfaces and Dependencies

No new runtime dependencies are required for the core unit tests.

Potential dependency additions (only if required to test existing behavior):

- If `src/qf_downloader/utils.py:file_checksum` is intended to be used and tested, add `aiofiles` to `pyproject.toml` so the module is importable and testable.

Existing dependencies to leverage:

- `pytest` and `pytest-mock` (already in `[project.optional-dependencies].dev` in `pyproject.toml`).
- `unittest.mock.AsyncMock` (standard library) for async fakes.
