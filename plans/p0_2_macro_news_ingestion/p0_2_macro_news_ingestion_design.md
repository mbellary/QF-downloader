# Phase 0.2 — Macro & News Ingestion (Design)

This document designs Phase 0 Task 0.2 (Macro & News ingestion) as specified in the ExecPlan:
- `plans/p0_2_macro_news_ingestion/p0_2_macro_news_ingestion_execplan.md`

It is intentionally Phase 0 scoped: **raw-only**, auditable, deterministic, idempotent, and explicitly bound to Quant Q0.1 (time alignment) and Q0.7 (provider allowlist) constraints.

## Inventory for the feature

This inventory lists the components expected to be affected by implementing Phase 0.2.

### Configuration and contracts

- `config/vendors/macro_feeds.json`
  - Current: does not exist.
  - Impact: new file defining *raw upstream endpoint specs* (URLs, params, auth mechanisms) for macro + news providers.

- `config/vendors/macro_providers.json`
  - Current: does not exist.
  - Impact: new file defining the *curated/allowlisted* provider set for Phase 0.2, aligned with Quant Q0.7 (`docs/quant/data_providers/macro_event_providers.yaml`). Providers not allowlisted must be present but `enabled=false`.

- `config/secrets/news_api.json` (gitignored) and `config/secrets/news_api.example.json` (committed)
  - Current: only FX secrets scaffolding exists.
  - Impact: add news API secret scaffolding (template + README update) and ensure it cannot be committed.

- `docs/infra/phase0/schemas/macro_news_ingestion.yaml`
  - Current: does not exist.
  - Impact: new schema/contract describing required metadata invariants for macro/news artifacts.

- `docs/quant/return_calculation.yaml` (Q0.1)
  - Current: exists and is treated as JSON-in-YAML in code.
  - Impact: Phase 0.2 metadata must include its hash + effective date, and must declare UTC binding.

- `docs/quant/data_providers/macro_event_providers.yaml` (Q0.7)
  - Current: exists.
  - Impact: source of truth allowlist; used to validate/curate `macro_providers.json`.

### Runtime code

- `src/qf_downloader/config.py`
  - Current: loads canonical provider config for FX (Phase 0.1).
  - Impact: extend to support Phase 0.2 provider config paths (macro/news) and optional secrets path, without breaking Phase 0.1.

- `src/qf_downloader/provider_config.py`
  - Current: loads provider configuration from JSON/YAML into a normalized dict shape.
  - Impact: may be extended to support Phase 0.2 specific fields (e.g., `artifact_type`, `date_query_mode`, `enabled`, and auth configuration).

- `src/qf_downloader/downloader.py` (`ProviderDownloader`)
  - Current: FX-oriented “pair/day” ingestion.
  - Impact: reused primitives (fetching, retries, checksuming patterns), but Phase 0.2 should avoid contorting FX assumptions; introduce a dedicated downloader for exogenous feeds.

- `src/qf_downloader/db.py` (`DownloadDB`)
  - Current: stores checksum ledger and failure records.
  - Impact: reuse for idempotence and failure recording for macro/news partitions.

- `src/qf_downloader/metadata.py`
  - Current: builds sidecar metadata for Phase 0.1 and rollup manifest under `pipelines/ingestion/fx/metadata.json`.
  - Impact: extend to support a Phase 0.2 schema id, macro/news artifact types, and a new rollup manifest (recommended) under `pipelines/ingestion/macro_news/metadata.json`.

- `src/qf_downloader/storage.py` (`S3Client`)
  - Current: supports AWS + LocalStack.
  - Impact: reused for macro/news artifacts if Phase 0.2 uploads to S3 like Phase 0.1.

- `src/qf_downloader/s3_indexer.py` (`S3Indexer`)
  - Current: indexes FX artifacts into DynamoDB.
  - Impact: optional for Phase 0.2 (recommended if we want parity with Phase 0.1); would need additional attributes for `artifact_type` (macro_events/news).

- New module: `src/qf_downloader/exogenous_downloader.py`
  - Current: does not exist.
  - Impact: new “exogenous” ingestion path that handles date ranges rather than FX pairs.

### CLI

- `src/qf_downloader/cli.py`
  - Current: FX-oriented commands.
  - Impact: add Phase 0.2 CLI commands to backfill macro/news by provider and date range, and enforce “no forward-looking” constraints by default.

### Tests

- `tests/unit/...`
  - Current: unit tests exist for Phase 0.1 and P0.4.
  - Impact: add unit tests for deterministic path derivation, metadata contents (UTC + spec hash), idempotence, and forward-looking range rejection.

- `tests/integration/...`
  - Current: LocalStack integration tests exist for Phase 0.1.
  - Impact: optional extension to cover macro/news if S3+DynamoDB indexing is used.

## Design for the feature

### Goals

- Deterministic raw artifact layout under:
  - `data/raw/macro/events/<provider>/<YYYY>/<MM>/<DD>/...`
  - `data/raw/news/<provider>/<YYYY>/<MM>/<DD>/...`
- Sidecar metadata for every artifact (`*.metadata.json`) including:
  - provenance (provider, request parameters, URL)
  - content hash (SHA-256)
  - ingestion timestamps in UTC
  - Quant contract binding: hash (+ effective_date if present) of `docs/quant/return_calculation.yaml`
  - schema id/version for Phase 0.2
- Idempotent reruns using checksum ledger (`DownloadDB`).
- No silent drops: errors (including 404/missing) recorded and auditable.
- Provider allowlist enforced by contract alignment with Q0.7.
- No embedded interpretation: no sentiment/scoring/labeling. Text normalization is mechanical only.

### Non-goals (Phase 0 constraints)

- No feature extraction, labeling, or event categorization.
- No bar/return construction.
- No entity extraction or topic modeling.

### Provider configuration model

Phase 0.2 uses two layers:

1) **Upstream feeds** (`config/vendors/macro_feeds.json`)
   - The “how to call the upstream API” layer.

2) **Curated providers** (`config/vendors/macro_providers.json`)
   - The “what we are allowed to ingest” layer.
   - Must align with Q0.7 allowlist. Non-allowlisted entries must be present but disabled.

Recommended minimal provider schema (conceptual):

- `name`: string
- `enabled`: bool
- `artifact_type`: `macro_events` | `news`
- `date_query_mode`: `day` | `range`
- `url_template`: string
- `params`: dict (may include `{start}`, `{end}`, `{date}` placeholders)
- `auth`:
  - `type`: `none` | `header_api_key` | `query_api_key` | `basic`
  - `env_var`: string (for secret lookup)
  - `header_name` / `query_param_name` where applicable
- `content_type_hint`: optional (metadata only)
- `retry`: optional overrides (max attempts, backoff)

### Storage layout and naming

We keep naming deterministic and partition by UTC day.

- Macro events:
  - Path prefix: `data/raw/macro/events/<provider>/<YYYY>/<MM>/<DD>/`
  - Filename: `macro_events_<YYYYMMDD>.json` (or `.ndjson` if the provider is streaming)

- News:
  - Path prefix: `data/raw/news/<provider>/<YYYY>/<MM>/<DD>/`
  - Filename: `news_<YYYYMMDD>.json`

For each artifact, write:

- raw artifact bytes to the file above
- sidecar metadata to: `<filename>.metadata.json`

If mechanical normalization is performed for news, store **both**:

- `news_<YYYYMMDD>.raw` (original bytes)
- `news_<YYYYMMDD>.json` (normalized text container)

### Exogenous ingestion flow

A new `ExogenousProviderDownloader` performs Phase 0.2 ingestion.

High-level flow (per provider + partition day):

```mermaid
flowchart TD
  A[CLI: macro-backfill/news-backfill] --> B[Load curated providers]
  B --> C{Provider enabled + allowlisted?}
  C -- no --> X[Skip with explicit message]
  C -- yes --> D[Resolve date range (UTC days)]
  D --> E[For each day: build request]
  E --> F[Fetch bytes (aiohttp + tenacity)]
  F --> G[Compute sha256]
  G --> H{Checksum already seen?}
  H -- yes --> I[Record skip (idempotent)]
  H -- no --> J[Write raw to deterministic path]
  J --> K[Upload to S3 (optional parity)]
  K --> L[Write sidecar metadata]
  L --> M[Append rollup manifest]
  F -->|HTTP 404/5xx| N[Record failure in DownloadDB]
```

### Idempotence and failure recording

- For each partitioned artifact, compute SHA-256 over the raw bytes.
- Use `DownloadDB` to check whether the checksum has already been ingested for `(provider, artifact_type, partition_day)`.
- On success, record a download row (including storage key/path and request URL).
- On failure (HTTP errors, decoding errors, validation errors), record failure rows keyed by `(provider, artifact_type, partition_day)`.

### “No forward-looking timestamps” enforcement

Default CLI behavior:

- If user does not specify `--end`, default to `yesterday_utc`.
- If user specifies an `--end` beyond `yesterday_utc`, reject.

Rationale: many macro providers include scheduled future events; storing them in Phase 0.2 would create accidental look-ahead.

### Metadata contract

Phase 0.2 sidecar metadata must include:

- `schema_id`: `infra.phase0.macro_news_ingestion`
- `schema_version`: semver or integer (start at `1`)
- `artifact_type`: `macro_events` | `news`
- `provider`: name
- `partition_date_utc`: `YYYY-MM-DD`
- `fetched_at_utc`: ISO-8601 timestamp
- `request`:
  - `url`
  - `params` (with secrets redacted)
  - `headers` (with secrets redacted)
- `content`:
  - `sha256`
  - `bytes`
  - `content_type` (best effort)
- `quant_contracts`:
  - `q0_1_return_calculation_sha256`
  - `q0_1_effective_date` (if present)
  - `timezone`: `UTC`

### Rollup manifest

Add a Phase 0.2 rollup manifest (append-only JSON) at:

- `pipelines/ingestion/macro_news/metadata.json`

Each entry points to the on-disk path and (if used) S3 key and includes the sidecar metadata pointer.

### Testing strategy (design-level)

Unit tests (must be offline):

- Path determinism for macro/news.
- “No forward-looking” default/rejection behavior.
- Metadata includes UTC binding and Quant spec hash.
- Idempotence: same bytes twice → second run skipped.

Integration tests (optional parity):

- LocalStack S3 write/read and DynamoDB index/query if Phase 0.2 uses `S3Indexer`.

### Implementation sequencing

- Add configuration contracts + secrets templates.
- Add schema contract for metadata.
- Implement exogenous downloader + CLI commands.
- Add unit tests and (optional) LocalStack integration tests.

