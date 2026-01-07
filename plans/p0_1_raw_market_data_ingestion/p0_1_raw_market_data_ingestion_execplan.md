# Phase 0.1 — Raw Market Data Ingestion (FX) ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository uses ExecPlans as specified in PLANS.md at the repository root. This document must be maintained in accordance with PLANS.md.

## Purpose / Big Picture

After this change, a user can ingest raw FX market data (tick and vendor-provided OHLCV where available) into a deterministic on-disk/S3 layout with an auditable metadata manifest, with all timestamps and session/timezone conventions explicitly bound to Quant’s Q0.1 contract.

A human can see it working by running the ingestion CLI against a known provider (initially Dukascopy) for a fixed date, then verifying:

1) the expected raw artifact(s) exist under the agreed output prefixes (tick vs ohlcv),

2) a sidecar metadata JSON exists for each artifact and includes the Quant Q0.1 spec hash + timezone convention (UTC), and

3) rerunning the same ingest is idempotent (no duplicates due to checksum ledger).

## Task Statement (from data_tasks.md)

### Description

Define and implement the canonical ingestion mechanism for raw FX market data, strictly aligned with Quant-defined return and session rules.

### Objective

Ensure raw market data is ingested once, timestamped once, and never reinterpreted downstream.

### Inputs

- Vendor API credentials: `/config/secrets/fx_api_keys.json` (Data Engineering)
- Vendor endpoint specs: `/config/vendors/fx_providers.json` (Data Engineering)
- Return calculation rules: `docs/quant/return_calculation.yaml` (Quant Q0.1)
- Session boundary rules: `docs/quant/return_calculation.yaml` (Quant Q0.1)
- Timezone conventions: `docs/quant/return_calculation.yaml` (Quant Q0.1)

### Deliverables

- Deterministic FX tick ingestion
- Deterministic FX OHLCV ingestion
- Timestamp normalization logic
- Raw-data metadata schema
- Missing-data & retry policy

### Outputs

- Raw FX tick data: `/data/raw/fx/tick/`
- Raw FX OHLCV data: `/data/raw/fx/ohlcv/`
- Ingestion metadata: `/pipelines/ingestion/fx/metadata.json`
- Raw Market Ingestion schema: `/docs/infra/phase0/schemas/raw_market_ingestion.yaml`

### Acceptance Criteria

- No timezone ambiguity
- No silent data drops
- Raw data reproducible from vendor + config alone

## Progress

- [x] (2026-01-05) Environment verified on Windows: `make check` and `make test SUITE=unit` pass on branch `docs/p0-1-raw-market-data-ingestion-execplan`.
- [x] (2026-01-05) GitHub tracking issue created: https://github.com/mbellary/QF-downloader/issues/12
- [x] (2026-01-05) Task branch: https://github.com/mbellary/QF-downloader/tree/task/p0-1-raw-market-data-ingestion
- [x] (2026-01-05) Design document created: `plans/p0_1_raw_market_data_ingestion/p0_1_raw_market_data_ingestion_design.md`
- [x] (2026-01-05) Unit tests added for Phase 0.1 design contracts (not executed in Tester mode): `tests/unit/test_p0_1_raw_market_ingestion.py`
- [x] (2026-01-05) Implemented Phase 0.1 ingestion behavior (deterministic paths, sidecar metadata, failure recording, artifact_type indexing):
  - Code: `src/qf_downloader/downloader.py`, `src/qf_downloader/metadata.py`, `src/qf_downloader/db.py`, `src/qf_downloader/s3_indexer.py`
- [x] (2026-01-05) Updated / added unit tests for Phase 0.1 contracts: `tests/unit/test_p0_1_raw_market_ingestion.py`, `tests/unit/test_provider_downloader.py`
- [x] (2026-01-05) Added / validated dockerized LocalStack integration coverage:
  - Harness: `tests/integration/conftest.py`
  - Boundaries: `tests/integration/test_localstack_boundaries.py`
  - Phase 0.1: `tests/integration/test_p0_1_raw_market_ingestion_integration.py`
  - Verified via: `make test SUITE=integration RUNTIME=docker PYTEST_ARGS='-rs'` (user-confirmed passing)

- [x] (2026-01-05) Implementation commit: https://github.com/mbellary/QF-downloader/commit/522e877
- [x] (2026-01-05) PR opened (Closes #12): https://github.com/mbellary/QF-downloader/pull/13

- [x] (2026-01-06) Added missing repo artifacts referenced by Task 0.1 Inputs/Outputs:
  - Vendor endpoint spec contract: `config/vendors/fx_providers.json`
  - Metadata schema contract: `docs/infra/phase0/schemas/raw_market_ingestion.yaml`

- [x] (2026-01-06) Added secrets scaffolding for Task 0.1 Inputs:
  - Local-only secrets contract path (gitignored): `config/secrets/fx_api_keys.json`
  - Committed template: `config/secrets/fx_api_keys.example.json`
  - Notes: `config/secrets/README.md`
  - Git safety: `.gitignore` ignores `config/secrets/*.json` but allows `*.example.json`

- [x] (2026-01-06) Validation: `make check` and `make test SUITE=unit` pass.

## Surprises & Discoveries

- Observation: The Quant Q0.1 spec file at `docs/quant/return_calculation.yaml` is JSON content stored in a `.yaml` file. YAML 1.2 parsers can load JSON, so `yaml.safe_load` is acceptable, but this should be called out explicitly in code/docstrings.
  Evidence: file begins with `{` and contains JSON object keys.

- Observation: Current `src/qf_downloader/providers.yaml` mixes FX tick/OHLCV providers and macro providers. Canonical Phase 0.1 config is now `config/vendors/fx_providers.json`; legacy YAML is deprecated.
  Evidence: providers include `econdb` and `fmp` entries of type `macro`.

## Decision Log

- Decision: Keep Phase 0.1 implementation additive and reuse the existing downloader skeleton (`src/qf_downloader/downloader.py`) rather than introducing a new ingestion framework.
  Rationale: The repo already has a working idempotent pattern (checksum ledger + S3 upload + DynamoDB index). Leveraging it reduces risk and keeps the implementation minimal.
  Date/Author: 2026-01-05 / Copilot

- Decision: Treat “timestamp normalization” as an auditable contract and metadata guarantee in Phase 0.1, not as full tick decoding for all providers.
  Rationale: Some vendor formats (e.g., Dukascopy `.bi5`) require non-trivial parsing. Phase 0.1 can still be compliant by (a) storing raw bytes immutably, (b) recording explicit vendor timestamp conventions and UTC binding in metadata, and (c) deferring deterministic bar construction to Task 0.3.
  Date/Author: 2026-01-05 / Copilot

- Decision: Track implementation via GitHub Issue #12.
  Rationale: Program Manager workflow requires Issue → Branch → PR traceability; this issue will remain the canonical artifact for Phase 0.1 execution.
  Date/Author: 2026-01-05 / Copilot

## Outcomes & Retrospective

- Implemented Phase 0.1 end-to-end (unit + LocalStack integration verified on Windows).
- Next: open PR linked to Issue #12 and proceed with review/merge workflow.

## Context and Orientation

This repository is a Python package (see `pyproject.toml`) that currently downloads per-provider daily payloads and uploads them to S3.

Key modules:

- `src/qf_downloader/cli.py`: Typer CLI with `list-providers`, `run` (polling), and `backfill`.
- `src/qf_downloader/downloader.py`: `ProviderDownloader` which formats a provider `url_template`, fetches bytes with `aiohttp`, deduplicates via SQLite (`DownloadDB`), uploads to S3 (`S3Client`), and indexes the file in DynamoDB (`S3Indexer`).
- `src/qf_downloader/db.py`: SQLite ledger for downloaded artifacts and a `fetch_status` table for last successful fetch timestamps.
- `src/qf_downloader/storage.py`: S3 client wrapper using `aioboto3`, supporting LocalStack when `APP_ENV=localstack`.
- `src/qf_downloader/s3_indexer.py`: DynamoDB indexer storing (pair, provider, date, s3_key) records.
- `config/vendors/fx_providers.json`: canonical provider definitions used by default by the CLI.

Quant contract dependency:

- `docs/quant/return_calculation.yaml` (Q0.1): defines UTC timezone convention, bar alignment rule, and missing-data policy requirements. Phase 0.1 must explicitly bind ingestion metadata to this contract.

Definitions used in this plan:

- “Raw artifact”: the exact bytes fetched from a vendor endpoint for a given instrument and time partition (e.g., a daily tick file), stored without transformation.
- “Sidecar metadata”: a small JSON file stored alongside a raw artifact describing provenance (provider, URL, fetch time, checksum), time conventions (UTC binding), and references to the Quant contract.
- “Deterministic layout”: a stable path scheme that can be derived solely from (provider config + instrument + date + artifact type) and does not depend on runtime randomness.

## Plan of Work

This section describes how to implement Task 0.1 in this repository, strictly within Phase 0 rules (no labels, no modeling logic). The plan is organized as milestones that are independently verifiable.

Before implementing any milestone, read the design document at `plans/p0_1_raw_market_data_ingestion/p0_1_raw_market_data_ingestion_design.md` and keep implementation consistent with that design (deterministic layout, metadata contract, failure recording).

### Milestone 1 — Introduce Phase 0.1 configuration contracts under `config/`

At the end of this milestone, the repository has explicit vendor and secrets configuration locations matching the Phase 0.1 task statement, and the runtime can load them.

Work:

- Create `config/vendors/fx_providers.json` (or `.yaml`) as the canonical FX market provider list for Phase 0.1.
- Create `config/secrets/fx_api_keys.json` as a local-only secrets file (excluded from git if not already) and document the required keys.
- Update `src/qf_downloader/config.py` to support these files in addition to (or as a replacement for) the current `PROVIDERS_FILE` env var.
- Update `src/qf_downloader/cli.py` so Phase 0.1 commands use the new config paths by default, while preserving backward compatibility for existing tests.

Notes / constraints:

- Do not hardcode OS-specific absolute paths.
- Secrets must not be committed; ensure `.gitignore` covers `config/secrets/*` if it does not already.

### Milestone 2 — Deterministic tick + OHLCV ingestion paths and provider config shape

At the end of this milestone, the ingestion path layout matches the task outputs:

- Tick artifacts land under `data/raw/fx/tick/<provider>/<pair>/<YYYY>/<MM>/<DD>/...`
- OHLCV artifacts land under `data/raw/fx/ohlcv/<provider>/<pair>/<YYYY>/<MM>/<DD>/...`

Work:

- Extend provider configuration to include:

  - `artifact_type`: one of `tick` or `ohlcv`
  - `instrument_format`: how to map `EURUSD` into URL placeholders (e.g., `{pair}` or `{base}`+`{quote}`)
  - Optional `content_encoding` / `format` fields (e.g., `dukascopy_bi5`) for metadata only

- Update `src/qf_downloader/downloader.py`:

  - Ensure URL template formatting supports `{base}` and `{quote}` in addition to `{pair}`.
  - Add explicit handling for query params / API keys when provider config includes them.
  - Ensure `save_path`/S3 key prefix is derived from artifact_type + provider + pair + date (deterministic and contract-bound).

- Update the DynamoDB index (`src/qf_downloader/s3_indexer.py` usage) to include `artifact_type` as an attribute (and optionally in the partition key), so tick and OHLCV can be queried independently.

### Milestone 3 — Timestamp normalization contract and raw metadata schema

At the end of this milestone, every ingested raw artifact produces a metadata record and a schema exists under the required docs path.

Work:

- Create `docs/infra/phase0/schemas/raw_market_ingestion.yaml` describing required metadata fields and invariants. Keep it simple: this is a contract schema for humans and downstream jobs.

- Implement metadata generation in a new module, e.g. `src/qf_downloader/metadata.py`, used by `ProviderDownloader`:

  - `sha256` checksum
  - provider name, URL, request headers summary (do not store secrets)
  - fetch timestamps (`fetched_at_utc` as ISO-8601)
  - partition keys: `pair`, `date` (YYYYMMDD), `artifact_type`
  - a copy of the time conventions that matter: `timezone=UTC`, `timestamp_unit=ISO-8601`
  - a hash of the Quant spec file contents (e.g., SHA-256 of `docs/quant/return_calculation.yaml`) and its `effective_date`

- Store per-artifact sidecar metadata next to the raw artifact path with a stable naming rule, e.g. `.../<filename>.metadata.json`.

- Create / update a roll-up ingestion metadata file at `pipelines/ingestion/fx/metadata.json` that lists ingested partitions and their metadata pointers. This file should be append-only and deterministic.

Important: Phase 0.1 should not compute returns or bars; it only binds time conventions and provenance.

### Milestone 4 — Missing-data + retry policy (no silent drops)

At the end of this milestone, failures are recorded in a way that can be audited, and retries are consistent.

Work:

- Keep HTTP retry behavior in `ProviderDownloader._fetch` (currently uses Tenacity). Make retry parameters explicit in provider config where reasonable.

- Add explicit failure recording:

  - Extend `src/qf_downloader/db.py` with a table to record fetch failures keyed by (provider, pair, date, artifact_type) with error class/message and last_attempt_at.
  - Ensure `ProviderDownloader._download_single_day` returns a structured result for success/skip/failure and that failures are persisted.

- Ensure that “missing file” outcomes are captured (e.g., 404 from vendor) and do not get swallowed.

### Milestone 5 — Tests and verification

At the end of this milestone, there are tests that prove the Phase 0.1 guarantees.

Work:

- Add unit tests under `tests/unit/` to cover:

  - Deterministic path construction for tick and OHLCV.
  - URL template formatting for `{pair}` and `{base}`/`{quote}`.
  - Metadata generation includes UTC binding and Quant spec hash.
  - Idempotence: repeated ingest attempts do not create duplicate DB rows for the same checksum.

- (Optional but recommended) Add an integration test under `tests/integration/` using LocalStack verifying:

  - S3 object exists at expected key.
  - DynamoDB index row exists and includes `artifact_type`.

## Concrete Steps

All commands below assume a Windows dev machine using bash (Git Bash) and that you are in the repository root.

0) Read the design document:

  - `plans/p0_1_raw_market_data_ingestion/p0_1_raw_market_data_ingestion_design.md`

1) Verify environment and baseline:

   - `git status -sb`
   - `uv --version`
   - `make check`
   - `make test SUITE=unit`

   Expected result: `make check` succeeds and unit tests report all passing.

2) Create a feature branch for implementation:

   - `git switch -c task/p0-1-raw-market-data-ingestion`

3) Run the CLI against a fixed provider/date once Milestones 1–3 are implemented:

   - Set `PROVIDERS_FILE` (or the new config path) and required AWS env vars.
   - Run a bounded backfill for one day (or a short range) and confirm artifacts exist.

   Expected result (illustrative): the command prints upload messages and returns without exceptions; rerunning prints “skipped” for already-downloaded artifacts.

## Validation and Acceptance

Acceptance is met when a human can verify all of the following:

- Timezone is unambiguous:

  - Sidecar metadata contains `timezone=UTC` and a reference (hash) to `docs/quant/return_calculation.yaml`.

- No silent drops:

  - Any fetch failure produces a persisted failure record (SQLite) and a structured CLI result.

- Reproducible from vendor + config alone:

  - Given `config/vendors/fx_providers.*`, a date, and the pair list, the raw artifact paths and URLs can be deterministically reconstructed.

- Tests:

  - `make test SUITE=unit` passes.
  - `make test SUITE=integration RUNTIME=docker` passes, including `tests/integration/test_p0_1_raw_market_ingestion_integration.py`.

In addition, the unit tests in `tests/unit/test_p0_1_raw_market_ingestion.py` must pass. These tests encode the Phase 0.1 design contracts:

- URL templates support `{base}`/`{quote}` placeholders derived from the `pair` string.
- Deterministic default layout under `data/raw/fx/<tick|ohlcv>/...` when `save_path` is not specified.
- Sidecar metadata upload occurs with a deterministic `.metadata.json` key.

The integration test in `tests/integration/test_p0_1_raw_market_ingestion_integration.py` must also pass. It encodes the LocalStack-backed contract:

- raw artifact object exists in S3 at the deterministic key
- sidecar metadata object exists in S3 at `<raw_key>.metadata.json`
- DynamoDB index entry exists and includes `artifact_type`

## Idempotence and Recovery

- Idempotence: rerunning ingestion for the same (provider, pair, date, artifact_type) should not create duplicates because checksums are recorded in SQLite and used to skip re-upload.

- Recovery from partial failure:

  - If S3 upload fails after fetch, rerun should reattempt upload (checksum ledger should only be written after successful upload + metadata write).
  - If metadata write fails after upload, rerun should detect missing sidecar metadata and repair it deterministically.

## Artifacts and Notes

- Planned new / updated artifact paths (repository-relative):

  - `config/vendors/fx_providers.json` (or `.yaml`)
  - `config/secrets/fx_api_keys.json` (local-only)
  - `docs/infra/phase0/schemas/raw_market_ingestion.yaml`
  - `pipelines/ingestion/fx/metadata.json`

- Existing code to extend:

  - `src/qf_downloader/downloader.py`
  - `src/qf_downloader/cli.py`
  - `src/qf_downloader/config.py`
  - `src/qf_downloader/db.py`
  - `src/qf_downloader/s3_indexer.py`

## Interfaces and Dependencies

Use existing dependencies only unless there is a clear gap:

- HTTP: `aiohttp`
- Retry: `tenacity`
- Config parsing: `PyYAML` (`yaml.safe_load` can parse JSON-as-YAML)
- Storage: `aioboto3`
- SQLite ledger: `aiosqlite`

New/changed interfaces to define (names are prescriptive):

- In `src/qf_downloader/metadata.py`:

  - `def quant_spec_sha256(path: str | Path) -> str`
  - `def build_raw_artifact_metadata(...)-> dict[str, object]`

- In `src/qf_downloader/downloader.py`:

  - Extend `_download_single_day` to accept `artifact_type: str` and to write sidecar metadata.
  - Extend URL formatting to support `{base}` and `{quote}`.


Change note: This ExecPlan file was created on 2026-01-05 to unblock Phase 0.1 implementation. It is intentionally conservative (metadata-first) to stay Phase 0 compliant while acknowledging that full tick decoding is provider-specific and may be introduced incrementally.
