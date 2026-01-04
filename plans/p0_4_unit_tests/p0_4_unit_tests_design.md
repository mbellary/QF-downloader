# Inventory for the feature

This design document covers the feature plan in `plans/p0_4_unit_tests/p0_4_unit_tests_execplan.md` and must be kept consistent with that ExecPlan.

## Components and modules affected

### `tests/unit/` (new + updates)

**Current functionality:**

- The repository currently contains `tests/unit/test_dummy_ci.py`, which is a placeholder test that only asserts `True`.

**Impact from this feature:**

- Replace placeholder tests with real unit tests that validate deterministic, offline behavior for key modules in `src/qf_downloader/`.
- Tests must not call the network, AWS, or Docker.

### `tests/test_cli_help.py` (update or migration)

**Current functionality:**

- Uses Click’s `CliRunner` against `qf_downloader.cli:cli`.
- `src/qf_downloader/cli.py` includes a minimal `click.Command` named `cli` purely for backwards compatibility with this test.

**Impact from this feature:**

- Decide whether to keep the shim or migrate tests to the real Typer app (`qf_downloader.cli:app`).
- If migrating, unit tests should validate `--help` output through Typer’s test runner and allow removal of the Click shim later.

### `src/qf_downloader/utils.py`

**Current functionality:**

- `ensure_dir(path)` creates a directory tree.
- `guess_content_type(url, filename)` returns a content-type guess.
- `file_checksum(path)` computes a hash asynchronously using `aiofiles`.

**Impact from this feature:**

- Add unit tests for `ensure_dir` and `guess_content_type`.
- Decide whether to (a) add `aiofiles` as a dependency and test `file_checksum`, or (b) refactor `file_checksum` to not require `aiofiles`.

### `src/qf_downloader/db.py`

**Current functionality:**

- `DownloadDB` is an async SQLite-backed checksum ledger with methods:
  - `init`, `close`, `exists_checksum`, `add_download`, `get_last_successful`.
- `Database` is a synchronous SQLite helper used by some integration flows.

**Impact from this feature:**

- Add unit tests that validate correctness and idempotence of `DownloadDB` using per-test temporary DB files.

### `src/qf_downloader/downloader.py`

**Current functionality:**

- `ProviderDownloader` orchestrates:
  - constructing provider URLs,
  - fetching bytes via `_fetch()` and `aiohttp.ClientSession`,
  - deduping via `DownloadDB.exists_checksum`,
  - upload via `S3Client.upload_file`,
  - indexing via `S3Indexer.index_file`.

**Impact from this feature:**

- Add unit tests for deterministic behavior by stubbing `_fetch()` and using async fakes for DB/S3/indexer.
- Validate both “skipped” and “uploaded” branches.

### `src/qf_downloader/storage.py`

**Current functionality:**

- `S3Client` is an async wrapper for put/head operations using `aioboto3` and `APP_ENV` switch.
- `LocalStorage` is a synchronous local disk storage helper.

**Impact from this feature:**

- No functional changes are required for unit tests.
- Unit tests may use a fake `S3Client` (AsyncMock) and may add small unit coverage for `LocalStorage` if useful.

### `pyproject.toml`

**Current functionality:**

- Defines runtime dependencies and `[project.optional-dependencies].dev` including pytest, pytest-cov, pytest-mock, ruff, boto3, localstack-client.
- Does not list `aiofiles` even though `src/qf_downloader/utils.py` imports it.

**Impact from this feature:**

- Potentially add `aiofiles` as a dependency (preferably runtime if `file_checksum()` is part of shipped functionality; otherwise dev-only plus refactor).

### `pytest.ini`

**Current functionality:**

- `testpaths = tests`
- `addopts = --cov=src --cov-report=xml` (writes `coverage.xml`)

**Impact from this feature:**

- Likely no changes required.
- Unit tests must remain compatible with the global coverage addopts.

### `Makefile`

**Current functionality:**

- Provides `make test` with parameters `SUITE` and `RUNTIME`.
- Unit tests default to `tests/unit` and integration tests to `tests/integration`.

**Impact from this feature:**

- No changes are strictly required for unit tests, but the Makefile may be enhanced later (in implementation) to add clearer targets like `make test-unit`.

---

# Design for the feature

## Goals and non-goals

**Goals**

- Provide unit tests that validate the “pure logic” and deterministic branches in `src/qf_downloader/`.
- Ensure unit tests are offline: no live HTTP requests, no Docker, no LocalStack, no real AWS.
- Keep tests OS-agnostic (Windows, macOS, Linux), using `tmp_path` for files and avoiding hard-coded paths.
- Ensure the default test runner produces `coverage.xml` via `pytest.ini` for CI parity.

**Non-goals**

- Do not validate LocalStack, S3, or DynamoDB behavior here (covered in the integration tests design).
- Do not add new runtime features or refactor production code unless required to make the code testable and consistent.

## Testing strategy (unit)

### Test structure

- Place new tests under `tests/unit/`.
- Follow pytest naming: `test_*.py` and `test_*` functions.
- Prefer “one behavior per test”, with small assertions and deterministic inputs.

### Isolation approach

- Patch/stub at the highest stable seam:
  - For `ProviderDownloader`, patch `ProviderDownloader._fetch()` to return deterministic bytes.
  - Use async fakes for `DownloadDB`, `S3Client`, and `S3Indexer` methods (`AsyncMock`).

This avoids brittle mocking of `aiohttp.ClientSession.request` and prevents network calls.

### Async handling

- Avoid adding `pytest-asyncio` initially.
- Use `asyncio.run(...)` inside tests when calling async functions.

This keeps dependency surface minimal and matches current repo conventions.

## Detailed design by module

### `src/qf_downloader/utils.py`

**`ensure_dir()`**

- Test idempotence: calling twice does not error.
- Verify directory exists after call.

**`guess_content_type()`**

- Case 1: With a filename extension that `mimetypes` recognizes (e.g., `file.csv`) returns `text/csv`.
- Case 2: With no filename, fallback from URL extension works for `.csv`, `.pdf`, `.html`.
- Case 3: Unknown extension returns `application/octet-stream`.

**`file_checksum()`**

- If we keep `aiofiles`, add `aiofiles` to `pyproject.toml` and test that checksum matches known content.
- If we choose to remove `aiofiles`, refactor `file_checksum` to use standard file I/O, but that is a production code change and should be justified and tested.

**Preferred design choice:** add `aiofiles` to dependencies to make existing code importable and testable.

### `src/qf_downloader/db.py:DownloadDB`

Design tests around a per-test SQLite file:

- Use `tmp_path / "test.db"`.
- Flow:
  - `db = DownloadDB(str(db_path))`
  - `asyncio.run(db.init())`
  - exercise methods
  - `asyncio.run(db.close())`

Key unit assertions:

- `exists_checksum(provider_key, checksum)` is false before insert and true after.
- `add_download(...)` updates `fetch_status` so `get_last_successful(provider_key)` becomes non-None.

### `src/qf_downloader/downloader.py:ProviderDownloader`

Create tests that cover the two core branches:

1) **New checksum (upload path)**

- Arrange:
  - provider dict with `name`, `supports_pairs`, `url_template`, `save_path`.
  - AsyncMock DB where `exists_checksum` returns `False`.
  - AsyncMock S3 where `upload_file` succeeds.
  - Fake indexer with async `index_file`.
  - Patch `_fetch` to return deterministic bytes.

- Assert:
  - return contains `status == "uploaded"`.
  - `s3.upload_file` called with expected `key` and content bytes.
  - `db.add_download` called with provider_key and computed checksum.
  - `indexer.index_file` called with provider/pair/date/s3_key.

2) **Existing checksum (skip path)**

- Arrange identical, but `exists_checksum` returns `True`.

- Assert:
  - return contains `status == "skipped"`.
  - `s3.upload_file`, `db.add_download`, and `indexer.index_file` are not called.

Also include direct unit tests for:

- `_prepare_headers()` with `header_api_key` auth when env var exists / does not exist.
- `_prepare_auth()` for `basic` auth when env vars exist / missing.

### CLI (`src/qf_downloader/cli.py`)

Design choice:

- Introduce a Typer-based help test that runs `qf_downloader.cli:app --help` and asserts commands appear.
- Keep the Click shim temporarily to avoid breaking existing tests; removal should be a separate, explicitly-scoped change.

## Makefile/CI/Docs alignment (design constraints)

- Unit test design assumes `pytest.ini` coverage addopts are always on.
- Unit tests must pass under `make test SUITE=unit RUNTIME=local`.
- Any doc updates required (e.g., removing `math_lib` references from `tests/AGENTS_TESTS.md`) are tracked in the unit test ExecPlan, but actual edits occur during implementation.

## Diagrams

### Unit-test isolation seams

    +---------------------------+
    | ProviderDownloader         |
    |  - _download_single_day()  |
    +-------------+-------------+
                  |
                  | patch `_fetch()` -> bytes
                  v
        +--------------------+
        | deterministic bytes |
        +--------------------+

    DB, S3, Indexer are fakes:

        DownloadDB.exists_checksum  -> AsyncMock
        DownloadDB.add_download     -> AsyncMock
        S3Client.upload_file        -> AsyncMock
        S3Indexer.index_file        -> AsyncMock

## Design compliance notes

- Formatting/linting: follow `src/qf_downloader/AGENTS_LINTING.md` (`uv run ruff format .` and `uv run ruff check .`).
- Testing execution: follow `tests/AGENTS_TESTS.md` but correct any stale package-name references during implementation.
- Commands should use `uv` (per `AGENTS_ENVIRONMENT.md`) and should be reproducible on Windows.
