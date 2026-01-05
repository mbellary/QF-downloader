# QF-downloader

Async downloader workers for ingesting daily provider payloads, deduplicating via a local SQLite ledger, and uploading artifacts to S3.

This repository currently implements a single concrete downloader pipeline in `qf_downloader.downloader.ProviderDownloader`:

- For each provider and each configured pair, fetch a URL derived from `url_template` and the current date
- Compute SHA-256 checksum, skip if already seen for `(provider, pair)`
- Upload bytes to S3 at a key derived from `save_path` + `{pair}_{yyyymmdd}.bin`

## Requirements

- Python `>=3.13` (per `pyproject.toml`)
- Recommended: `uv`
- For integration tests: Docker + Docker Compose (LocalStack)

## Install

```bash
uv sync --venv .venv
```

Then run commands via `uv run ...`.

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
- `PROVIDERS_FILE`: path to providers YAML (recommended: `./src/qf_downloader/providers.yaml`)
- `POLL_INTERVAL_SECONDS`: default poll interval for providers without `poll_interval`

Note: the code has a placeholder default for `PROVIDERS_FILE` in `qf_downloader.config`; in practice you should set `PROVIDERS_FILE` or pass `--providers-file`.

## Provider YAML format (what the current code supports)

The downloader expects a YAML file with a top-level `providers:` list.

Minimal example:

```yaml
providers:
  - name: dukascopy
    supports_pairs: ["EURUSD", "USDJPY"]
    url_template: "https://example.invalid/{pair}/{year}/{month}/{day}.bin"
    save_path: "raw/dukascopy/{pair}/{year}/{month}/{day}"
    method: GET
    poll_interval: 3600
    auth: {}
```

Supported fields:

- `name` (required)
- `supports_pairs` (required): list of strings; the current implementation iterates directly over this list
- `url_template` (required): must be compatible with `.format(pair=..., year=..., month=..., day=...)`
- `save_path` (required): used to build the S3 key prefix via `.format(pair=..., year=..., month=..., day=...)`
- `method` (optional): defaults to `GET`
- `poll_interval` (optional): overrides global `POLL_INTERVAL_SECONDS`
- `auth` (optional):
  - `type: header_api_key` with `header_env` + optional `header_name`
  - `type: basic` with `user_env` + `pass_env`

Important limitations (as of today):

- “Enabled/disabled” flags in YAML are not honored; if a provider appears in the list it will be processed.
- URL templates that require other placeholders (e.g. `{api_key}`) are not supported by the current downloader and will raise formatting errors.

## CLI

The CLI is implemented with Typer in `qf_downloader.cli`.

List providers:

```bash
uv run -- python -m qf_downloader.cli list-providers --providers-file src/qf_downloader/providers.yaml
```

Run incremental polling (infinite loop):

```bash
uv run worker_incremental -- --providers-file src/qf_downloader/providers.yaml
```

Run a bounded historical backfill for a single provider:

```bash
uv run -- python -m qf_downloader.cli backfill --provider-name dukascopy --years 3 --providers-file src/qf_downloader/providers.yaml
```

You can also use the script entrypoint that exposes the Typer app:

```bash
uv run worker_historical -- backfill --provider-name dukascopy --years 3
```

## LocalStack (integration tests)

The integration suite uses LocalStack for S3 + DynamoDB.

Run integration tests in Docker (recommended / most reproducible):

```bash
make test SUITE=integration RUNTIME=docker
```

Run only unit tests (no Docker):

```bash
make test SUITE=unit
```

If you don’t have `make` available, the underlying unit-test command is:

```bash
uv run --dev -- python -m pytest tests/unit -vv
```

## Notes

- S3 uploads are performed via `aioboto3` in `qf_downloader.storage.S3Client`.
- Checksums and dedupe tracking are stored in SQLite via `qf_downloader.db.DownloadDB`.

