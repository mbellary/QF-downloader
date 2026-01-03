# P0.1 — Raw Market Data Ingestion Specification & Pipeline

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, the repo will have a single, deterministic, auditable ingestion path for raw FX market data (tick + OHLCV) that downstream code can consume without re-interpreting timestamps, session boundaries, or vendor-specific quirks. The observable outcome is that running the ingestion CLI produces raw data files under `data/raw/fx/tick/` and `data/raw/fx/ohlcv/` plus a metadata ledger (local and/or remote) that proves exactly what was fetched, when it was fetched, how timestamps were normalized (to UTC), and what gaps/retries occurred.

This task produces infrastructure only; it must not compute labels, returns, signals, or features. Its job is to make later work reproducible.

## Progress

- [x] (2026-01-03 00:00Z) Created initial ExecPlan for P0.1.
- [x] (2026-01-03 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/QF-downloader/issues/1
- [x] (2026-01-03 00:00Z) Bootstrapped local dev environment with `uv pip install -e ".[dev]"`.
- [x] (2026-01-03 00:00Z) Ran environment verification commands and recorded current repo status (format/lint/test discovery).
- [ ] Repo hygiene dependency: make Ruff clean + add `tests/` layout so environment checklist passes end-to-end (tracking: https://github.com/mbellary/QF-downloader/issues/3).
- [ ] Populate `config/vendors/fx_providers.json` using the Quant-approved provider list in `docs/quant/data_providers/return_calculation_providers.yaml` (Dukascopy, TrueFX, Alpha Vantage, Stooq).
- [ ] Add infra schema artifact: `docs/infra/phase0/schemas/raw_market_ingestion.yaml`.
- [ ] Implement tick ingestion pipeline (fetch → normalize timestamps → write raw artifact → emit metadata → upload/index if configured).
- [ ] Implement OHLCV ingestion pipeline (same contract as tick ingestion).
- [ ] Add missing-data detection + retry policy that is observable (no silent drops).
- [ ] Add unit tests for timestamp normalization + metadata emission.
- [ ] Add integration path (optional): LocalStack-backed S3 + DynamoDB smoke test.

## Surprises & Discoveries

- Observation: The current repository uses `src/qf_downloader/providers.yaml` for provider catalogs, but Phase 0 tasks specify JSON-based config files under `/config/vendors/*.json`.
  Evidence: `src/qf_downloader/cli.py` loads YAML via `yaml.safe_load`, while `data_tasks.md` specifies `/config/vendors/fx_providers.json`.

- Observation: Quant has an explicit approved-provider list for FX price data.
  Evidence: `docs/quant/data_providers/return_calculation_providers.yaml` lists Dukascopy, TrueFX, Alpha Vantage, and Stooq as approved providers for bid/ask prices.

- Observation: Tracking issue created in the target implementation repo.
  Evidence: https://github.com/mbellary/QF-downloader/issues/1

- Observation: The repository is not currently clean under Ruff format/lint, and pytest does not currently collect any tests.
  Evidence: `uv run ruff format --check .` reports multiple files “Would reformat”; `uv run ruff check .` reports import ordering/unused imports; `pytest.ini` sets `testpaths = tests` but there is no `tests/` directory yet.

## Decision Log

- Decision: Reuse the existing “download → dedupe → persist → (optional) upload/index” architecture already implemented by `ProviderDownloader` (`src/qf_downloader/downloader.py`), but split “provider definition” (config) from “ingestion contract” (schemas + metadata ledger) so Phase 0 outputs become binding for later phases.
  Rationale: Minimizes new surface area while making outputs auditable and contract-bound.
  Date/Author: 2026-01-03 / Copilot

- Decision: Normalize all persisted timestamps to UTC and make the normalization explicit and testable.
  Rationale: Phase 0 acceptance criteria require “no timezone ambiguity”; UTC normalization plus explicit metadata is the most enforceable interpretation.
  Date/Author: 2026-01-03 / Copilot

- Decision: Restrict Phase 0 FX market ingestion to Quant-approved providers: Dukascopy, TrueFX, Alpha Vantage, and Stooq.
  Rationale: Phase 0 outputs are binding inputs to later phases; using only approved providers prevents the system from drifting to unvetted data quality.
  Date/Author: 2026-01-03 / Copilot

- Decision: Track this ExecPlan via a dedicated GitHub issue in `mbellary/QF-downloader` and link it from `Progress`.
  Rationale: Keeps Phase 0 implementation tracking tied to the living plan without duplicating status across multiple places.
  Date/Author: 2026-01-03 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

This repository currently provides an async ingestion worker that:

- Loads a provider catalog from YAML (`src/qf_downloader/cli.py`, `PROVIDERS_FILE` in `src/qf_downloader/config.py`).
- Downloads provider artifacts per (pair, day) (`ProviderDownloader` in `src/qf_downloader/downloader.py`) using `aiohttp` with `tenacity` retries.
- Deduplicates downloads via a local SQLite checksum ledger (`DownloadDB` in `src/qf_downloader/db.py`).
- Uploads raw payloads to S3 (`S3Client` in `src/qf_downloader/storage.py`) and indexes them in DynamoDB (`S3Indexer` in `src/qf_downloader/s3_indexer.py`).

Phase 0 Task 0.1 expands this into a contract-bound “raw market ingestion” primitive:

- “Raw” means: vendor-provided data with only mechanical normalization (especially timestamp normalization and file naming/partitioning). No modeling logic, no engineered features, no labels.
- “Deterministic” means: given the same vendor config + credentials, the pipeline produces identical raw artifacts and identical metadata for the same date range.
- “Auditable” means: metadata proves what was fetched (URL/request parameters, response checksums), and missing-data handling is explicit.

This task must align with Quant-defined return + session rules:

- `docs/quant/return_calculation.yaml` is the authoritative source for timezone conventions and session boundary semantics.

Terminology used in this plan:

- Tick data: per-update market quotes/trades at irregular timestamps.
- OHLCV bars: fixed-interval bars containing open/high/low/close/volume at a regular cadence.
- Normalized timestamp: the canonical timestamp stored in the output artifact, in UTC, with an explicit mapping from any source timezone.
- Ingestion metadata: a machine-readable record of what was fetched, normalized, and persisted.

## Task Spec Snapshot (from data_tasks.md)

### Description

Define and implement the canonical ingestion mechanism for raw FX market data, strictly aligned with Quant-defined return and session rules.

### Objective

Ensure raw market data is ingested once, timestamped once, and never reinterpreted downstream.

### Inputs

- Vendor API credentials (Data Engineering): `/config/secrets/fx_api_keys.json`
- Vendor endpoint specs (Data Engineering): `/config/vendors/fx_providers.json`
- Return calculation rules (Quant Q0.1): `/docs/quant/return_calculation.yaml`
- Session boundary rules (Quant Q0.1): `/docs/quant/return_calculation.yaml`
- Timezone conventions (Quant Q0.1): `/docs/quant/return_calculation.yaml`

Quant-approved provider list:

- FX price providers (Quant Q0.1 data providers): `docs/quant/data_providers/return_calculation_providers.yaml`

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

## Plan of Work

Implement Phase 0 ingestion as a thin, explicit layer on top of the current downloader primitives.

1. Add Phase 0 configuration files under `config/` (new directory). These are the binding contracts for what gets fetched and how it is interpreted mechanically.

   - `config/secrets/fx_api_keys.json`: a key-value map of provider names → API keys (or references). This must never be committed with real secrets; provide a checked-in `*.example` template.
   - `config/vendors/fx_providers.json`: a provider catalog describing endpoints, auth mechanism, supported instruments, and the payload type (tick vs OHLCV) and timestamp fields.

     This file must be derived from the Quant-approved provider list in `docs/quant/data_providers/return_calculation_providers.yaml`. Concretely: only these provider names may appear as ingestion sources for this task:

     - Dukascopy
     - TrueFX
     - Alpha Vantage
     - Stooq

2. Add a Phase 0 schema under `docs/infra/phase0/schemas/raw_market_ingestion.yaml` describing:

   - required metadata fields (provider, instrument, requested window, observed timestamp window, checksum, storage URI/path)
   - canonical timestamp normalization rule (UTC)
   - expected raw tick schema (field names and types) and OHLCV schema
   - gap handling policy fields (missing intervals, retries attempted, final status)

3. Extend the Python package with Phase 0 ingestion modules that:

   - Load vendor config (JSON) + secrets (JSON and/or env overrides).
   - Fetch raw data deterministically for a defined (pair, start, end, cadence) spec.
   - Normalize timestamps to UTC (mechanical transformation only).
   - Persist raw outputs to `data/raw/fx/tick/` and `data/raw/fx/ohlcv/` using a stable partitioning scheme.
   - Write/update an ingestion metadata ledger at `pipelines/ingestion/fx/metadata.json` (append-only JSONL is also acceptable if justified, but the task calls it `.json`; pick one format and codify it in the schema).
   - Reuse existing dedupe logic where possible (checksum ledger and/or S3/DynamoDB indexing).

4. Add CLI entry points (Typer) so the pipeline is observable and runnable:

   - A bounded backfill command for tick and OHLCV.
   - An incremental “poll today” command may be reused from the existing `run` loop if it can be made to call the new ingestion contract.

5. Add tests that prove timezone normalization and gap detection behavior.

## Concrete Steps

All commands below assume the repository root as the working directory.

1. Environment bootstrap:

   Preferred local workflow is defined in `AGENTS_ENVIRONMENT.md`.

   - Create a feature branch (do not work on `main`):

     git checkout -b feature/p0-1-raw-market-ingestion

   - Install dev dependencies in editable mode (creates/uses `.venv/`):

     uv pip install -e ".[dev]"

   - Verification checklist (must be clean before PRs):

     uv run ruff format --check .
     uv run ruff check .
     uv run pytest --cov

   Notes:

   - On Windows, prefer `uv run ...` to avoid manual activation.
   - If you do activate manually, PowerShell activation is typically:

     .\.venv\Scripts\Activate.ps1

2. Add configuration templates (checked in) and document how to supply real secrets locally:

   - Create `config/secrets/fx_api_keys.json.example`.
   - Create `config/vendors/fx_providers.json`.
   - Update `README.md` “Configuration” section to reference the new config files (do not remove `.env` support; allow env overrides).

3. Add schema artifact:

   - Create `docs/infra/phase0/schemas/raw_market_ingestion.yaml`.

4. Implement ingestion modules (new files) and wire into CLI:

   - In `src/qf_downloader/cli.py`, add commands such as:

     - `ingest_fx_tick_backfill(provider_name: str, start: str, end: str, ...)`
     - `ingest_fx_ohlcv_backfill(provider_name: str, start: str, end: str, ...)`

   - Add new modules under `src/qf_downloader/` (exact naming is an implementation detail, but keep them small and explicit). Suggested structure:

     - `src/qf_downloader/ingestion_fx.py` (config loading + orchestration)
     - `src/qf_downloader/timestamp_normalization.py` (UTC normalization utilities)
     - `src/qf_downloader/metadata_ledger.py` (write/update `pipelines/ingestion/fx/metadata.json`)

   - Reuse:

     - `src/qf_downloader/downloader.py` for HTTP fetch + retry mechanics
     - `src/qf_downloader/db.py` for dedupe and last-successful markers
     - `src/qf_downloader/storage.py` and `src/qf_downloader/s3_indexer.py` for optional S3 + DynamoDB outputs

5. Add tests:

   - Create `tests/unit/test_timestamp_normalization.py`.
   - Create `tests/unit/test_metadata_ledger.py`.
   - Run `make test SUITE=unit`.

Expected (illustrative) transcript once tests exist:

    [pytest] APP_ENV=production uv run --dev -- python -m pytest tests/unit
    ...
    10 passed in 1.23s

## Validation and Acceptance

Acceptance is met when a human can run the ingestion pipeline and observe:

- Timezone correctness:

  - The persisted artifact timestamps are in UTC.
  - The metadata ledger records `source_timezone` (if applicable) and `normalized_timezone = UTC`.

- No silent drops:

  - For a requested window, the metadata ledger records either:
    - a complete coverage statement (e.g., “all expected hourly bars present”), or
    - explicit missing intervals and the retry attempts made.

- Reproducibility:

  - Re-running ingestion for the same provider/instrument/window does not create conflicting duplicates.
  - Checksums and dedupe logic prevent re-uploading identical payloads.

Validation commands:

- `make test SUITE=unit`
- Optional integration (LocalStack): `APP_ENV=localstack make test SUITE=integration RUNTIME=docker`

Environment validation commands (must pass before opening a PR):

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest --cov`

## Idempotence and Recovery

- Ingestion commands must be safe to re-run:

  - If data already exists (by checksum or exact-key match), the pipeline must skip or no-op and still record an audit event (or re-emit a “skipped” record) without corrupting the ledger.

- If a run fails midway:

  - Partial artifacts must be either written atomically (write temp → rename) or explicitly marked as partial in metadata.
  - The next run must be able to resume (by reading the ledger and/or `DownloadDB.get_last_successful`).

## Artifacts and Notes

Expected new or updated artifacts after implementation:

- `config/secrets/fx_api_keys.json.example`
- `config/vendors/fx_providers.json`
- `docs/infra/phase0/schemas/raw_market_ingestion.yaml`
- `pipelines/ingestion/fx/metadata.json`
- `data/raw/fx/tick/` (directory)
- `data/raw/fx/ohlcv/` (directory)
- New ingestion modules under `src/qf_downloader/` as described above
- Unit tests under `tests/unit/`

## Interfaces and Dependencies

Internal interfaces to preserve and reuse:

- `ProviderDownloader` in `src/qf_downloader/downloader.py` for download/retry plumbing.
- `DownloadDB` in `src/qf_downloader/db.py` for dedupe and last-successful markers.
- `S3Client` in `src/qf_downloader/storage.py` and `S3Indexer` in `src/qf_downloader/s3_indexer.py` for optional object storage + indexing.

External dependencies:

- Quant rules: `docs/quant/return_calculation.yaml` (timezone + session semantics).
- Quant-approved FX provider list: `docs/quant/data_providers/return_calculation_providers.yaml`.
- Vendor endpoints + auth (Phase 0 config): `config/vendors/fx_providers.json` and `config/secrets/fx_api_keys.json`.

Task dependencies:

- Hard dependency: Q0.1 artifacts exist in this repo already (`docs/quant/return_calculation.yaml`) and must be treated as authoritative for timezone and session boundary conventions.
- No temporal dependency on other Phase 0 tasks; however, this task must keep outputs compatible with later Phase 0 Task 0.3 (master timeseries construction), so the tick/OHLCV schemas must be stable and unambiguous.
