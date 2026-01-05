# Inventory for the feature

This feature is Phase 0 Task 0.1 (“Raw Market Data Ingestion Specification & Pipeline”) from `data_tasks.md`. It is focused on ingesting *raw* FX market data artifacts deterministically and audibly, without any downstream interpretation (no returns, no labeling, no features).

The current repository already has a downloader skeleton that (a) fetches daily provider payload bytes, (b) deduplicates by SHA-256 checksum in SQLite, (c) uploads to S3, and (d) indexes the S3 key in DynamoDB.

Below is an inventory of modules and artifacts that will be affected.

## Existing code modules

- `src/qf_downloader/cli.py`

  - Current functionality: Provides Typer commands (`list-providers`, `run`, `backfill`) that read a YAML providers file and orchestrate polling/backfill using `ProviderDownloader`.
  - Impact: Needs Phase 0.1-specific entry points and/or defaults so that FX ingestion uses the canonical Phase 0.1 vendor spec (`config/vendors/fx_providers.*`) and does not accidentally ingest macro providers.

- `src/qf_downloader/config.py`

  - Current functionality: Loads env vars and sets defaults like `DB_PATH` and `PROVIDERS_FILE`.
  - Impact: Must support Phase 0.1 configuration contract paths (vendor spec + secrets) and expose them to runtime/CLI without hard-coded absolute paths.

- `src/qf_downloader/downloader.py` (`ProviderDownloader`)

  - Current functionality: For a given provider and each supported pair, formats `url_template` with `{pair}/{year}/{month}/{day}`, fetches bytes, dedupes by checksum, uploads to S3, writes ledger row, and indexes in DynamoDB.
  - Impact:

    - Needs to separate artifact types (`tick` vs `ohlcv`) and enforce deterministic storage layout under `data/raw/fx/<tick|ohlcv>/...`.
    - Needs URL template formatting support for `{base}` and `{quote}` in addition to `{pair}`.
    - Needs explicit, auditable metadata generation (sidecar + roll-up) that binds timezone and Quant Q0.1 contract hash.
    - Needs explicit failure recording for “no silent drops”.

- `src/qf_downloader/db.py` (`DownloadDB`)

  - Current functionality: Stores downloads and a last-successful timestamp per provider.
  - Impact:

    - Needs schema extensions for Phase 0.1, including artifact_type partitioning and a failure table that records errors per (provider, pair, date, artifact_type).
    - Needs to preserve idempotence semantics and remain compatible with unit tests.

- `src/qf_downloader/storage.py` (`S3Client`)

  - Current functionality: Uploads bytes to S3 via `aioboto3`, supports LocalStack and production.
  - Impact: May need to upload both the raw artifact and its sidecar metadata JSON (as a separate object) with deterministic keys.

- `src/qf_downloader/s3_indexer.py` (`S3Indexer`)

  - Current functionality: Writes DynamoDB items keyed by `pk=pair#provider` and `sk=date#s3_key`, and supports querying by date range.
  - Impact: Needs to include `artifact_type` (at minimum as an attribute; ideally in the partition key) so tick and OHLCV series can be queried independently.

- `src/qf_downloader/utils.py`

  - Current functionality: Directory creation and content-type guessing.
  - Impact: May be reused for deterministic path building and stable content types for metadata objects.

- `src/qf_downloader/providers.yaml`

  - Current functionality: Mixed list of FX and macro providers.
  - Impact: Should not be the canonical contract for Phase 0.1 because it mixes tasks; Phase 0.1 will introduce a separate canonical FX vendor spec under `config/vendors/`.

## Existing tests

- `tests/unit/test_provider_downloader.py`

  - Current functionality: Validates upload/skip behavior for `_download_single_day` and auth header/basic auth helpers.
  - Impact: Must be updated/expanded to cover the new deterministic path scheme, URL placeholder behavior (`{base}/{quote}`), sidecar metadata generation, and failure recording semantics.

- `tests/unit/test_db_download_db.py`

  - Current functionality: Validates checksum dedupe tracking.
  - Impact: May need extensions if DB schema changes (e.g., artifact_type columns).

## New files / artifacts (Phase 0.1)

- `config/vendors/fx_providers.json` (or `config/vendors/fx_providers.yaml`)

  - Purpose: Canonical Phase 0.1 FX vendor spec (endpoints and storage rules).

- `config/secrets/fx_api_keys.json`

  - Purpose: Local-only secrets file referenced by config; must not be committed.

- `src/qf_downloader/fx_provider_config.py` (new)

  - Purpose: Typed parsing and validation of Phase 0.1 provider specs, with explicit support for placeholders, params, and artifact_type.

- `src/qf_downloader/metadata.py` (new)

  - Purpose: Construct and serialize sidecar metadata, compute Quant spec hash, and update the roll-up manifest.

- `docs/infra/phase0/schemas/raw_market_ingestion.yaml` (new)

  - Purpose: Human-readable contract schema for per-artifact metadata fields.

- `pipelines/ingestion/fx/metadata.json` (new)

  - Purpose: Deterministic roll-up manifest listing ingested partitions and pointers to sidecar metadata.


# Design for the feature

This design implements Task 0.1 as an additive extension of the existing downloader skeleton. The core principle is “raw bytes are immutable”; Phase 0.1 adds deterministic partitioning and contract-bound metadata.

## Goals (and non-goals)

Goals:

- Deterministic ingestion of FX raw artifacts for:

  - tick payloads (e.g., Dukascopy daily tick file)
  - vendor-provided OHLCV payloads (where available)

- Deterministic layout:

  - Local path base: `./data/raw/fx/<tick|ohlcv>/<provider>/<pair>/<YYYY>/<MM>/<DD>/...`
  - S3 key base: `data/raw/fx/<tick|ohlcv>/<provider>/<pair>/<YYYY>/<MM>/<DD>/...`

- Metadata binding:

  - Sidecar metadata JSON per artifact
  - Roll-up manifest `pipelines/ingestion/fx/metadata.json`
  - Explicit UTC binding and Quant Q0.1 spec hash (file: `docs/quant/return_calculation.yaml`)

- No silent drops:

  - Persist per-partition failures in SQLite with error + HTTP status
  - Expose structured status from CLI

Non-goals (explicitly excluded by Phase 0 rules):

- Parsing tick formats (e.g., Dukascopy `.bi5`) into rows
- Computing returns, features, labels, or “cleaned” time series
- Constructing canonical bars (that belongs to Task 0.3)

## High-level flow

End-to-end flow for one partition (provider, pair, date, artifact_type):

    Provider spec + inputs (pair/date)
              |
              v
      Resolve URL + request params
              |
              v
        Fetch raw bytes (retry)
              |
              v
      Compute sha256 checksum
              |
       +------+- exists? ------+
       |                      |
       v                      v
    Skip (idempotent)     Upload raw object
                              |
                              v
                       Write sidecar metadata
                              |
                              v
                       Update roll-up manifest
                              |
                              v
                       Index object in DynamoDB

Failure handling:

- Any exception or non-2xx response is recorded in SQLite `fetch_failures` keyed by (provider, pair, date, artifact_type), including the last error, last_attempt_at_utc, and HTTP status if present.

## Configuration contracts

Phase 0.1 requires two explicit config artifacts:

1) Vendor spec: `config/vendors/fx_providers.yaml` (or `.json`)

2) Secrets file: `config/secrets/fx_api_keys.json` (local-only)

### Provider spec schema (design)

The provider spec is designed to be easy to validate and deterministic.

Top-level:

- `version`: string
- `supported_pairs`: map of groups to list of instruments (optional; can be embedded per provider)
- `providers`: list of provider specs

Provider spec fields:

- `name`: stable identifier
- `enabled`: boolean
- `artifact_type`: `tick` or `ohlcv` (Phase 0.1 only)
- `supports_pairs`: list of `EURUSD`-style instruments
- `url_template`: string with supported placeholders:

  - `{pair}`: e.g., `EURUSD`
  - `{base}`: e.g., `EUR`
  - `{quote}`: e.g., `USD`
  - `{year}`, `{month}`, `{day}` (zero-padded strings)

- `method`: default `GET`
- `save_path_template`: optional; if absent, derived from the deterministic layout rule (preferred)
- `params`: optional mapping:

  - static key/values
  - API key by env or secrets lookup

- `auth`: optional, existing types supported today (header api key, basic)
- `retry`: optional mapping overriding retry attempts and backoff
- `format`: optional string used only for metadata provenance, e.g. `dukascopy_bi5`

### Secrets resolution

Keys should not appear in provider YAML. Resolution order:

1) Explicit environment variables (CI / production)
2) `config/secrets/fx_api_keys.json` (local dev)

Design choice: implement secrets resolution in a small helper module so that tests can override via env vars easily.

## Deterministic path scheme

Introduce a single source of truth function:

- `build_partition_prefix(artifact_type, provider, pair, day) -> str`

Returns a normalized forward-slash path *without* leading slash:

- `data/raw/fx/tick/dukascopy/EURUSD/2026/01/05`

Introduce filename rules:

- Raw filename: `<pair>_<YYYY><MM><DD>.<ext>`

  - Extension comes from provider `format` when known (e.g., `.bi5`) or defaults to `.bin`.

- Sidecar metadata filename: `<raw_filename>.metadata.json`

Keys:

- Raw object key: `<prefix>/<raw_filename>`
- Sidecar object key: `<prefix>/<raw_filename>.metadata.json`

Local filesystem:

- Use `Settings.download_path` (already exists in `src/qf_downloader/config.py`) as base. Local raw file is written to:

  - `<download_path>/<prefix>/<raw_filename>`

This allows Phase 0.1 acceptance checks to verify local `/data/raw/...` output even if S3 is not configured.

## Metadata contract

Per-artifact metadata JSON is the “timestamp normalization contract” for Phase 0.1.

Required fields:

- `schema_id`: `infra.phase0.raw_market_ingestion`
- `schema_version`: semantic version
- `provider`, `artifact_type`, `pair`, `date` (`YYYYMMDD`)
- `source`:

  - `url`
  - `http_method`
  - `request_headers_redacted`: (no secrets)

- `hashes`:

  - `sha256`: checksum of raw bytes

- `time_contract`:

  - `timezone`: `UTC`
  - `timestamp_unit`: `ISO-8601`
  - `quant_spec_path`: `docs/quant/return_calculation.yaml`
  - `quant_spec_sha256`: sha256(file bytes)
  - `quant_effective_date`: from the spec content

- `storage`:

  - `local_path` (optional in production)
  - `s3_bucket` and `s3_key` (optional in local-only mode)

- `ingested_at_utc`: ISO-8601 timestamp

The schema file `docs/infra/phase0/schemas/raw_market_ingestion.yaml` documents these fields and invariants.

### Roll-up manifest (`pipelines/ingestion/fx/metadata.json`)

To keep this deterministic and idempotent without introducing new dependencies:

- The manifest is a JSON object with:

  - `schema_version`
  - `generated_at_utc`
  - `entries`: array of per-partition entries

- On update:

  - Load existing manifest if present
  - Upsert by a stable key: `(provider, artifact_type, pair, date)`
  - Sort entries by `(provider, artifact_type, pair, date)`
  - Write back the full JSON

This is safe for single-process ingestion and deterministic for acceptance.

## Failure recording (no silent drops)

Extend `DownloadDB` with a new table:

- `fetch_failures(provider TEXT, pair TEXT, date TEXT, artifact_type TEXT, url TEXT, http_status INTEGER, error_type TEXT, error_message TEXT, attempt_count INTEGER, last_attempt_at_utc TEXT, PRIMARY KEY(provider, pair, date, artifact_type))`

Rules:

- Any exception or non-2xx response results in an upsert into `fetch_failures`.
- A successful ingestion should clear or supersede the failure record for that partition (design choice: either delete on success, or keep failures and add a `resolved_at_utc`). For Phase 0.1 minimality, delete-on-success is acceptable.

CLI should surface failures via structured output and non-zero exit code for batch commands when any partition fails.

## DynamoDB indexing changes

Current index keys:

- `pk = f"{pair}#{provider}"`
- `sk = f"{date}#{s3_key}"`

Phase 0.1 requires distinguishing tick vs ohlcv without scanning. Preferred design:

- `pk = f"{pair}#{provider}#{artifact_type}"`
- `sk = f"{date}#{s3_key}"`

And include `artifact_type` as an attribute.

Migration approach:

- During a transition period, write both pk shapes (two items) or implement pk change behind a flag.
- Since Phase 0 is foundational and the index is not yet widely consumed, it is acceptable to switch pk shape with a one-time LocalStack integration test update.

## CLI design

Keep UX minimal and avoid introducing new pages/flows:

- Maintain existing `backfill` command shape, but add an explicit flag to select the Phase 0.1 vendor spec:

  - `--providers-file` remains supported.
  - If omitted, Phase 0.1 FX commands default to `config/vendors/fx_providers.yaml`.

- Ensure macro providers are not ingested by Phase 0.1 commands.

## Testing strategy (per tests/AGENTS_TESTS.md)

Unit tests (required):

- Deterministic key/path builder
- URL formatting supports `{pair}` and `{base}/{quote}`
- Metadata contains UTC binding and Quant spec hash
- Failure recording on exception and on HTTP 404
- Idempotence remains: checksum skip behavior unchanged

Integration tests (optional, recommended):

- LocalStack S3: raw + sidecar objects exist
- LocalStack DynamoDB: indexed item contains correct pk/sk and `artifact_type`

All tests must pass via:

- `make check`
- `make test SUITE=unit`

## Diagram: module responsibilities

    cli.py
      |
      v
    fx_provider_config.py  ---->  config.py (paths + env)
      |
      v
    downloader.py (ProviderDownloader)
      |     |        |
      |     |        +--> metadata.py (sidecar + manifest)
      |     +--> db.py (downloads + failures)
      +--> storage.py (S3 raw + metadata)
            |
            +--> s3_indexer.py (DynamoDB index)

## Implementation notes (guardrails)

- Use `uv` for execution and dependency management.
- Do not introduce new dependencies unless strictly necessary.
- Keep code changes additive and preserve existing public interfaces where possible.
- Ensure all new functions have type annotations and are Ruff clean.
- Do not embed any modeling logic; Phase 0 outputs are contracts for later phases.
