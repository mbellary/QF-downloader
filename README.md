# MT5 Downloader

Lightweight, asynchronous ingestion workers that pull FX/market data from multiple providers, deduplicate on checksum, upload artifacts to S3, and index metadata locally (SQLite) and remotely (DynamoDB) for downstream processing.

## Table of Contents
1. [Project Highlights](#project-highlights)
2. [Architecture Overview](#architecture-overview)
3. [Data Flows](#data-flows)
4. [Quickstart](#quickstart)
5. [Configuration](#configuration)
6. [Provider Definitions](#provider-definitions)
7. [CLI Usage](#cli-usage)
8. [Local Development](#local-development)
9. [Testing & Quality](#testing--quality)
10. [Operational Notes](#operational-notes)
11. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Project Highlights
- Async-first pipeline built on `aiohttp`, `aioboto3`, and `aiosqlite` for efficient IO.
- Dual-mode workers: continuous incremental polling and bounded historical backfills.
- S3 uploads with content-type detection plus DynamoDB indexing through the `S3Indexer` helper.
- Local checksum store (`DownloadDB`) prevents duplicate downloads per provider/pair.
- Environment-driven configuration with `.env.prod` / `.env.dev` loading built into `config.py`.
- Typer-powered CLI (`qf_downloader.cli`) exposes ergonomic commands (`list-providers`, `run`, `backfill`).

---

## Architecture Overview

```
┌────────────────┐    ┌─────────────┐    ┌───────────┐    ┌────────────┐
│ Providers YAML │──▶│ Typer CLI   │──▶│ Downloader │──▶│ S3 (raw data)│
└────────────────┘    │ (run/backfill│    │ (per pair)│    └────────────┘
               └─────┬───────┘    └────┬──────┘            │
                   │                 │                   ▼
                   │                 │            ┌──────────────┐
                   ▼                 ▼            │ DynamoDB tbl │
               ┌──────────┐      ┌──────────┐       │ (S3 index)  │
               │ Download │◀────│ S3Client │       └──────────────┘
               │ DB (SQLite)     └──────────┘
               └──────────┘
```

*Key modules*
- `cli.py` orchestrates polling loops, backfill ranges, and utility commands.
- `downloader.py` contains `ProviderDownloader`, the async worker handling fetch → checksum → upload → index.
- `storage.py` wraps `aioboto3` for S3 uploads with automatic bucket/key resolution.
- `db.py` keeps a local SQLite ledger of checksums for deduplication.
- `s3_indexer.py` writes per-file metadata to DynamoDB (`RAW_FILE_INDEX_TABLE`).
- `config.py` centralizes env parsing and `.env` loading.

---

## Data Flows

### Incremental polling (existing flow)
1. `uv run worker_incremental` (or `python -m qf_downloader.cli run`) loads the providers file defined by `PROVIDERS_FILE`.
2. For each provider, `_run_loop()` spawns an async task respecting the provider-level or default `POLL_INTERVAL_SECONDS`.
3. Each iteration downloads files for all declared `supports_pairs` for the current UTC day, writes to a temp dir under `./data`, and computes a SHA-256 checksum.
4. If the checksum is new for `provider_name + pair`, the payload is uploaded to `s3://S3_BUCKET/<save_path>/{pair}_{yyyymmdd}.bin`, and metadata is recorded in SQLite + DynamoDB.
5. The loop sleeps for the configured interval and repeats indefinitely.

### Historical backfill (existing flow)
1. `uv run worker_historical -- --provider-name ... --years N` (or `python -m qf_downloader.cli backfill ...`) selects a single provider definition.
2. `_do_backfill()` walks day-by-day across the requested window (defaults to last 5 years) and reuses `_download_single_day()` for every pair/date combination.
3. The same dedupe → upload → index pipeline applies, ensuring historical gaps are filled without re-downloading files already present in the checksum ledger.

Both flows share the same storage, logging, and indexing primitives, so parity between real-time and replayed data is guaranteed.

---

## Quickstart

Prerequisites
- Python 3.13+
- AWS credentials with `s3:PutObject` + DynamoDB write permissions (or LocalStack for testing)
- Optional: Docker + Docker Compose for local AWS emulation

1. **Install uv (recommended)**
  ```bash
  python -m pip install --user uv
  # or
  pipx install uv
  ```

2. **Sync dependencies**
  ```bash
  uv sync --venv .venv
  # activate if desired
  source .venv/bin/activate  # Linux/macOS
  .venv\\Scripts\\activate   # Windows
  ```

3. **Populate configuration**
  - Copy `.env.prod` / `.env.dev` templates inside `src/qf_downloader/`.
  - Export any overrides in your shell or via `.env` files.

4. **Run a command**
  ```bash
  uv run worker_incremental -- --providers-file src/qf_downloader/providers.yaml
  ```

If you prefer not to use `uv`, run `python -m qf_downloader.cli run ...` inside an activated virtual environment.

---

## Configuration

`config.py` automatically loads `.env.dev` when `APP_ENV=localstack` and `.env.prod` otherwise. Key variables:

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | `production` or `localstack`; controls which `.env` is loaded | `production` |
| `S3_BUCKET` | Destination bucket for raw files | `None` (required) |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Explicit credentials (omit when using IAM roles) | `None` |
| `AWS_REGION` | Region for S3/DynamoDB clients | `us-east-1` |
| `LOCALSTACK_URL` | Endpoint URL when targeting LocalStack | `None` |
| `RAW_FILE_INDEX_TABLE` | DynamoDB table for the S3 index entries | `us-east-1` (placeholder) |
| `DB_PATH` | SQLite ledger path | `./data/downloads.db` |
| `PROVIDERS_FILE` | Path to YAML provider definition | `./src/example_pkg/providers.yaml` |
| `POLL_INTERVAL_SECONDS` | Global fallback polling cadence | `300` |
| `*_API_KEY` | Optional API keys injected by providers via env references | empty string |

> Tip: wrap secrets with AWS Parameter Store or Vault when deploying in production and only fall back to `.env` locally.

---

## Provider Definitions

Provider catalogs live in YAML files such as `src/qf_downloader/providers.yaml` or `src/qf_downloader/providers_single_pair.yaml`. A minimal entry looks like:

```yaml
providers:
  - name: dukascopy
   supports_pairs: ["EURUSD", "GBPUSD"]
   url_template: "https://data.provider.com/{pair}/{year}/{month}/{day}.bi5"
   save_path: "dukascopy/{pair}/{year}/{month}/{day}"
   method: GET
   poll_interval: 600
   auth:
    type: header_api_key
    header_name: X-API-KEY
    header_env: DUKASCOPY_API_KEY
```

Fields:
- `supports_pairs`: list of pairs, `ALL`, or a nested structure your downloader recognizes.
- `url_template`: uses `{pair}`, `{year}`, `{month}`, `{day}` placeholders; extend the template for provider-specific partitions.
- `save_path`: mirrored folder structure in S3/local staging before upload.
- `auth`: currently supports `header_api_key` and `basic`. Additional auth strategies can be added in `ProviderDownloader._prepare_headers/_prepare_auth`.
- `poll_interval`: overrides the default poll cadence per provider.

---

## CLI Usage

All commands live under the Typer app declared in `cli.py`.

| Command | Description | Example |
|---|---|---|
| `list-providers` | Print the parsed providers from a YAML file | `uv run python -m qf_downloader.cli list-providers --providers-file src/qf_downloader/providers.yaml` |
| `run` | Start the long-running incremental polling loop for every provider | `uv run worker_incremental -- --providers-file src/qf_downloader/providers.yaml` |
| `backfill` | Re-download data for a provider across the last _N_ years | `uv run worker_historical -- --provider-name dukascopy --years 3` |

Notes:
- All CLI parameters have sensible defaults derived from `config.py`.
- `worker_historical` currently points to `qf_downloader.cli:app` in `pyproject.toml`. Most users remap it to `qf_downloader.cli:backfill` for direct invocation; adjust `[project.scripts]` if needed.
- Arguments passed after `--` go straight to Typer, which keeps the `uv run` experience clean.

---

## Local Development

### Local AWS stack (optional)
1. Install Docker Desktop.
2. Start LocalStack and any supporting containers:
  ```bash
  docker compose -f docker-compose.test.yml up --build
  ```
3. Export `APP_ENV=localstack` so `config.py` loads `.env.dev` and points SDK clients to `LOCALSTACK_URL`.

### Useful helper scripts
- `python src/qf_downloader/downloader_test.py --url https://httpbin.org/html --out ./tmp/test.html` verifies basic download/write behavior.
- `uv run python -m qf_downloader.cli list-providers` validates YAML parsing and env resolution.

### Formatting & linting
- Ruff is preconfigured (`pyproject.toml` → `[tool.ruff]`). Run `uv run ruff check .` to lint and `uv run ruff format .` if you enable the formatter rule set.

---

## Testing & Quality

All verification flows are orchestrated through the repository Makefile so every run shares the same setup, execution, coverage, and teardown steps.

- **Bootstrap dependencies** once with `make setup` (wraps `uv sync --venv .venv`).
- **Local unit tests**: `make test SUITE=unit` executes everything under `tests/unit` without Docker.
- **Local integration tests**: point to LocalStack or AWS by exporting the right env (e.g., `APP_ENV=localstack make test SUITE=integration`).
- **Docker-orchestrated integration/E2E**: `APP_ENV=localstack make test SUITE=integration RUNTIME=docker` spins up the stack defined in `docker-compose.test.yml`, runs the suite, and automatically tears it down.
- **Coverage**: `make coverage SUITE=all` enables `pytest-cov` with XML + terminal output (writes `coverage.xml`).
- **Explicit teardown/cleanup**: `make teardown RUNTIME=docker` stops any lingering containers and removes `.pytest_cache`, `.coverage`, and `coverage.xml`.

> Pass extra pytest flags via `PYTEST_ARGS="-m 'not slow'" make test ...` as needed.

---

## Operational Notes

- **SQLite ledger**: `DB_PATH` defaults to `./data/downloads.db`. Persist this file between deployments to preserve dedupe information.
- **S3 uploads**: `ProviderDownloader` writes to a temporary local directory mirroring `save_path` before calling `S3Client.upload_file`. Ensure the bucket exists and lifecycle policies match retention requirements.
- **DynamoDB index**: `S3Indexer` expects `RAW_FILE_INDEX_TABLE` and writes `{provider, pair, date, s3_key}` items for downstream consumers.
- **Logging**: `logger.py` emits JSON-friendly structured logs. Set `LOG_LEVEL` env (if added) or rely on the default INFO level.
- **Credentials**: Prefer IAM roles in production. If you must supply static keys, scope them to the needed services and avoid checking `.env` files into VCS.
- **Backpressure**: For providers with strict rate limits, raise `poll_interval` or add throttling logic in `_download_single_day`.

---

## FAQ & Troubleshooting

**Downloads are skipped even though files are missing in S3**  
`ProviderDownloader` checksums the payload before upload. Delete the row from the SQLite DB (or change the provider+pair identifier) if you intentionally need to re-download.

**`worker_historical` exits immediately**  
Ensure `[project.scripts] worker_historical` points to a callable (e.g., `qf_downloader.cli:backfill`) or invoke via `python -m qf_downloader.cli backfill`.

**LocalStack uploads fail with SSL errors**  
Export `AWS_ENDPOINT_URL` (or update `storage.py` to honor `LOCALSTACK_URL`) and disable SSL verification if necessary; most issues stem from mismatched endpoints.

**Need to add another provider**  
Duplicate an entry in `providers.yaml`, update `url_template`, `save_path`, and any auth references, then rerun `list-providers` to validate.

---

## License

Add your preferred OSS license text or link here (e.g., MIT, Apache-2.0).
