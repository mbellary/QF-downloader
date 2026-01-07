# QF-downloader

[![Run Tests](https://img.shields.io/github/actions/workflow/status/mbellary/QF-downloader/full_pipeline.yml?branch=main&label=Run%20Tests)](https://github.com/mbellary/QF-downloader/actions/workflows/full_pipeline.yml)
[![codecov](https://codecov.io/gh/mbellary/QF-downloader/graph/badge.svg?branch=main)](https://codecov.io/gh/mbellary/QF-downloader)
![Python](https://img.shields.io/badge/python-%E2%89%A53.13-blue)

Production-oriented, async ingestion workers for downloading daily provider payloads, deduplicating via a local SQLite ledger, and uploading immutable raw artifacts to S3.

## What this provides (Phase 0.1)

Phase 0.1 adds a deterministic **raw FX ingestion contract**:

- Deterministic partitioning by `artifact_type` (`tick` vs `ohlcv`)
- URL templating supports `{pair}` and `{base}`/`{quote}` placeholders
- Per-artifact sidecar metadata (`<raw_key>.metadata.json`) bound to the Quant Q0.1 time contract
- Optional roll-up manifest at `pipelines/ingestion/fx/metadata.json` (runtime-generated)
- No silent drops: fetch failures are persisted in SQLite
- DynamoDB indexing optionally includes `artifact_type` in the partition key

At a high level, the downloader pipeline in `qf_downloader.downloader.ProviderDownloader`:

- For each provider and each configured pair, fetch a URL derived from `url_template` and the current date
- Compute SHA-256 checksum, skip if already seen for `(provider, pair)`
- Upload bytes to S3 at a key derived from `save_path` (or a deterministic default) + `{pair}_{yyyymmdd}.bin`
- Upload a metadata sidecar JSON to `<raw_key>.metadata.json`

## Requirements

- Python `>=3.13` (per `pyproject.toml`)
- Recommended: `uv`
- For integration tests: Docker + Docker Compose (LocalStack)

## Install

```bash
make setup
```

Then run commands via `uv run ...`.

## Development workflow

Run formatting + lint:

```bash
make format
make lint
```

Run the full local check (format-check + lint + tests):

```bash
make check
```

Run tests:

```bash
make test SUITE=unit
make test SUITE=integration RUNTIME=docker
```

Generate coverage:

```bash
make coverage
```

## Configuration

Runtime config is environment-driven and loaded by `qf_downloader.config`:

- If `APP_ENV=localstack`, it loads `src/qf_downloader/.env.dev`
- Otherwise, it loads `src/qf_downloader/.env.prod`

Common env vars:

- `APP_ENV`: `production` (default) or `localstack`
- `S3_BUCKET`: target bucket name (required)
- `AWS_REGION`: defaults to `us-east-1`
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: required for LocalStack, optional in production (IAM role / AWS profile supported)
- `LOCALSTACK_URL`: e.g. `http://localhost:4566`
- `DB_PATH`: defaults to `./data/downloads.db`
- `PROVIDERS_FILE`: path to providers config (recommended: `./config/vendors/fx_providers.json`)
- `POLL_INTERVAL_SECONDS`: default poll interval for providers without `poll_interval`

Note: the code has a placeholder default for `PROVIDERS_FILE` in `qf_downloader.config`; in practice you should set `PROVIDERS_FILE` or pass `--providers-file`.

### Phase 0.1 contract artifacts

These artifacts are added as part of Phase 0.1 to make the ingestion contract explicit:

- Vendor endpoint spec contract (wired into the CLI/runtime loader): `config/vendors/fx_providers.json`
- Sidecar metadata schema contract: `docs/infra/phase0/schemas/raw_market_ingestion.yaml`
- Secrets scaffolding:
  - Template (committed): `config/secrets/fx_api_keys.example.json`
  - Notes: `config/secrets/README.md`
  - Local-only secrets file (NOT committed): `config/secrets/fx_api_keys.json`

Secrets should be provided via environment variables in CI/production. For local development, copy the example:

```bash
cp config/secrets/fx_api_keys.example.json config/secrets/fx_api_keys.json
```

Then populate the values.

## Provider config format (JSON-first)

The downloader expects a config file with a top-level `providers` list.

Preferred format is JSON (the canonical contract): `config/vendors/fx_providers.json`.

Legacy YAML is still loadable for backwards compatibility, but is considered deprecated:

- `src/qf_downloader/providers.yaml`
- `src/qf_downloader/providers_single_pair.yaml`

Minimal example:

```json
{
  "providers": [
    {
      "name": "dukascopy",
      "enabled": true,
      "artifact_type": "tick",
      "supports_pairs": ["EURUSD", "USDJPY"],
      "url_template": "https://example.invalid/{pair}/{year}/{month}/{day}.bin",
      "method": "GET",
      "auth": {},
      "params": {}
    }
  ]
}
```

Supported fields:

- `name` (required)
- `supports_pairs` (required): list of strings; the current implementation iterates directly over this list
- `artifact_type` (recommended): `tick` or `ohlcv` (if absent, the code falls back to `type`)
- `url_template` (required): supports `.format(pair=..., base=..., quote=..., year=..., month=..., day=...)`
  - `pair` accepts `EURUSD` and `EUR/USD`
- Additional supported template vars:
  - `start_date` / `end_date` in `YYYY-MM-DD` format
- `save_path` (optional): used to build the S3 key prefix via `.format(...)`
  - If omitted, the downloader uses a deterministic default:
    - `data/raw/fx/<artifact_type>/<provider>/<pair>/<YYYY>/<MM>/<DD>`
- `method` (optional): defaults to `GET`
- `poll_interval` (optional): overrides global `POLL_INTERVAL_SECONDS`
- `params` (optional): mapping used for query params and template vars
  - `api_key_env`: if set, injects `{api_key}` template var from the named environment variable
- `auth` (optional):
  - `type: header_api_key` with `header_env` + optional `header_name`
  - `type: basic` with `user_env` + `pass_env`
  - `type: query_api_key` with `api_key_env` + optional `key_param_name` (defaults to `apikey`)

Notes:

- The CLI and runtime now honor `enabled: false` and skip disabled providers.

## CLI

The CLI is implemented with Typer in `qf_downloader.cli`.

List providers:

```bash
uv run -- python -m qf_downloader.cli list-providers --providers-file config/vendors/fx_providers.json
```

Run incremental polling (infinite loop):

```bash
uv run worker_incremental -- --providers-file config/vendors/fx_providers.json
```

Run a bounded historical backfill for a single provider:

```bash
uv run -- python -m qf_downloader.cli backfill --provider-name dukascopy --years 3 --providers-file config/vendors/fx_providers.json
```

You can also use the script entrypoint that exposes the Typer app:

```bash
uv run worker_historical -- backfill --provider-name dukascopy --years 3
```

## Docker (development)

You can run the same CLI commands from this README in Docker using the dev
compose stack in `docker-compose.yml`.

Bring up LocalStack (and optionally Prometheus + the app container):

```bash
docker compose up -d localstack
docker compose up -d prometheus qf_app
```

Run the module CLI (equivalent to `uv run -- python -m qf_downloader.cli ...`):

```bash
docker compose run --rm qf_app -- python -m qf_downloader.cli list-providers \
  --providers-file /qf-downloader/config/vendors/fx_providers.json
```

Run incremental polling (equivalent to `uv run worker_incremental -- ...`):

```bash
docker compose run --rm qf_app worker_incremental -- \
  --providers-file /qf-downloader/config/vendors/fx_providers.json
```

Run historical backfill (equivalent to `uv run worker_historical -- backfill ...`):

```bash
docker compose run --rm qf_app worker_historical -- backfill \
  --provider-name dukascopy --years 3 \
  --providers-file /qf-downloader/config/vendors/fx_providers.json
```

Stop the dev stack:

```bash
docker compose down
```

## LocalStack (integration tests)

The integration suite uses LocalStack for S3 + DynamoDB.

Run integration tests in Docker (recommended / most reproducible):

```bash
make test SUITE=integration RUNTIME=docker
```

This uses the repository root `docker-compose.test.yml`.

GitHub Actions also runs a dockerized integration job using `docker/docker-compose.test.yml`. That compose file runs pytest via:

```bash
uv run --dev -- python -m pytest
```

This avoids failures where `pytest` is not on `PATH` inside the container.

Run only unit tests (no Docker):

```bash
make test SUITE=unit
```

Run format + lint + tests together:

```bash
make check
```

If you don’t have `make` available, the underlying unit-test command is:

```bash
uv run --dev -- python -m pytest tests/unit -vv
```

## CI

GitHub Actions runs:

- Ruff format check
- Ruff lint
- Unit tests
- Dockerized integration tests (LocalStack)

Workflow definition: `.github/workflows/full_pipeline.yml`.

## Notes

- S3 uploads are performed via `aioboto3` in `qf_downloader.storage.S3Client`.
- Checksums and dedupe tracking are stored in SQLite via `qf_downloader.db.DownloadDB`.

### Phase 0.1 operational notes

- Sidecar metadata schema: see `docs/infra/phase0/schemas/raw_market_ingestion.yaml`.
- Runtime-generated roll-up manifest: `pipelines/ingestion/fx/metadata.json` (this file can be created/updated during ingestion runs).
- Failure recording: the SQLite DB includes a `fetch_failures` table keyed by `(provider, pair, date, artifact_type)`.

