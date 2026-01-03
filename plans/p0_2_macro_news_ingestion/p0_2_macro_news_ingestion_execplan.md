# P0.2 — Macro & News Ingestion Specification

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, the repo will ingest exogenous macroeconomic and news data as raw, timestamped, alignment-ready inputs with no embedded interpretation (no sentiment, no scoring, no labeling). The observable outcome is that a user can run a bounded backfill command to populate `data/raw/news/` and `data/raw/macro/events/` plus an auditable metadata ledger describing the source, request parameters, normalized timestamps (UTC), and any gaps/retries.

This task produces infrastructure only; downstream Quant attribution (Q0.7) and modeling tasks must consume these artifacts without needing to “guess” how timestamps were normalized or which vendor fields were used.

## Progress

- [x] (2026-01-03 00:00Z) Created initial ExecPlan for P0.2.
- [x] (2026-01-03 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/QF-downloader/issues/2
- [ ] Populate `config/vendors/macro_feeds.json` using the Quant-approved macro provider list in `docs/quant/data_providers/macro_event_providers.yaml` (FRED, ECB Calendars, Trading Economics (free metadata)).
- [ ] (blocked) Confirm which news-text vendors are approved for Phase 0 ingestion (Quant has not provided an approved news provider list under `docs/quant/data_providers/` as of 2026-01-03).
- [ ] Add infra schema artifact: `docs/infra/phase0/schemas/macro_news_ingestion.yaml`.
- [ ] Implement raw news ingestion (fetch → normalize text → normalize timestamps → persist → emit metadata).
- [ ] Implement raw macro event ingestion (fetch → normalize timestamps → persist → emit metadata).
- [ ] Add gap detection + retry policy and make it observable (no silent drops).
- [ ] Add unit tests for timestamp normalization and “no interpretation” constraints.

## Surprises & Discoveries

- Observation: The repo already has environment variables for some macro-style APIs (`FRED_API_KEY`, `FMP_API_KEY`) in `src/qf_downloader/config.py`, but Phase 0 tasks specify file-based config under `/config/secrets/news_api.json` and `/config/vendors/macro_feeds.json`.
  Evidence: `src/qf_downloader/config.py` defines multiple `*_API_KEY` env vars; `data_tasks.md` references JSON files under `/config/`.

- Observation: Quant has an explicit approved-provider list for macro event timing/metadata, but not for news text sources.
  Evidence: `docs/quant/data_providers/macro_event_providers.yaml` lists approved providers (FRED, ECB Calendars, Trading Economics (free metadata)), while there is no corresponding “news” provider artifact under `docs/quant/data_providers/`.

- Observation: Tracking issue created in the target implementation repo.
  Evidence: https://github.com/mbellary/QF-downloader/issues/2

## Decision Log

- Decision: Implement macro/news ingestion using the same core persistence and audit conventions as the market ingestion pipeline (P0.1): UTC-normalized timestamps, stable file naming/partitioning, and an explicit ingestion metadata ledger.
  Rationale: Downstream alignment and auditability depend on consistent conventions across Phase 0.
  Date/Author: 2026-01-03 / Copilot

- Decision: Treat text normalization as purely mechanical formatting (decode, normalize whitespace, preserve original content), and explicitly forbid computed fields like sentiment, topics, or scores.
  Rationale: The task requires “no embedded interpretation or labeling”.
  Date/Author: 2026-01-03 / Copilot

- Decision: Restrict Phase 0 macro event ingestion to Quant-approved providers: FRED, ECB Calendars, and Trading Economics (free metadata).
  Rationale: Q0.7 macro attribution depends on event timestamps and classifications; using the approved set keeps provenance stable and audit-ready.
  Date/Author: 2026-01-03 / Copilot

- Decision: Track this ExecPlan via a dedicated GitHub issue in `mbellary/QF-downloader` and link it from `Progress`.
  Rationale: Keeps Phase 0 implementation tracking tied to the living plan without duplicating status across multiple places.
  Date/Author: 2026-01-03 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The repository’s current ingestion system is primarily oriented around FX market data:

- `src/qf_downloader/cli.py` runs provider-based polling/backfills.
- `src/qf_downloader/downloader.py` provides `ProviderDownloader` with HTTP fetch + retries.
- `src/qf_downloader/db.py` provides `DownloadDB` for a checksum ledger and last-successful markers.
- `src/qf_downloader/storage.py` and `src/qf_downloader/s3_indexer.py` support S3 uploads + DynamoDB indexing.

Phase 0 Task 0.2 introduces a parallel ingestion stream for macro events and news text. It must be alignment-ready, which means:

- Every record/event must have a canonical UTC timestamp.
- The pipeline must preserve provenance (vendor name, endpoint, request window, and raw fields).
- The pipeline must not add any interpretive fields.

This task must align with Quant’s alignment rules:

- `docs/quant/return_calculation.yaml` defines timezone conventions and session boundary semantics, which should be referenced for timestamp normalization.

Terminology used in this plan:

- Macro event: a dated/time-stamped release (e.g., CPI) with fields like “actual/forecast/previous”, as provided by a vendor.
- News item: a time-stamped textual record, potentially with a headline/body and optional metadata like source/publisher.
- Alignment-ready: timestamps are normalized to UTC and the record contains enough context to align to market bars later.

## Task Spec Snapshot (from data_tasks.md)

### Description

Define ingestion of exogenous macroeconomic and news data with no embedded interpretation or labeling.

### Objective

Provide clean, timestamped, alignment-ready macro inputs for later Quant-defined attribution (Q0.7).

### Inputs

- News API credentials (LLM Team): `/config/secrets/news_api.json`
- Macro data vendor specs (LLM Team): `/config/vendors/macro_feeds.json`
- Quant alignment rules (Quant Q0.1): `/docs/quant/return_calculation.yaml`

Quant-approved provider list:

- Macro event providers (Quant Q0.7 data providers): `docs/quant/data_providers/macro_event_providers.yaml`

### Deliverables

- Raw news ingestion
- Raw macro event ingestion
- Text normalization (no sentiment, no scoring)

### Outputs

- Raw news text: `/data/raw/news/`
- Raw macro events: `/data/raw/macro/events/`
- Macro News Ingestion schema: `/docs/infra/phase0/schemas/macro_news_ingestion.yaml`

### Acceptance Criteria

- No forward-looking timestamps
- No implicit event labeling
- Event timestamps auditable

## Plan of Work

1. Add Phase 0 macro/news configuration files under `config/` (new directory, shared with P0.1).

   - `config/secrets/news_api.json.example`: template for local development.
   - `config/vendors/macro_feeds.json`: vendor catalog defining endpoints, auth, event schema mapping, and timestamp fields.

     This file must be derived from the Quant-approved provider list in `docs/quant/data_providers/macro_event_providers.yaml`. Concretely: only these provider names may appear as macro-event ingestion sources for this task:

     - FRED
     - ECB Calendars
     - Trading Economics (free metadata)

   The implementation must support env-var overrides for deployment parity (the repo already uses `.env.prod`/`.env.dev` loading in `src/qf_downloader/config.py`).

2. Add a schema artifact under `docs/infra/phase0/schemas/macro_news_ingestion.yaml` that defines:

   - canonical timestamp normalization (UTC)
   - required provenance fields (vendor/source, request window)
   - raw macro event shape (required keys, allowed optional keys)
   - raw news record shape (headline/body/source timestamps)
   - constraints prohibiting interpretive fields (explicitly list disallowed fields like `sentiment`, `score`, `label`, `topic_probability`)

3. Implement ingestion modules and wire them into the CLI.

   Suggested module layout (keep minimal and explicit):

   - `src/qf_downloader/ingestion_macro_news.py` (orchestration, config loading)
   - `src/qf_downloader/timestamp_normalization.py` (shared with P0.1)
   - `src/qf_downloader/metadata_ledger.py` (shared with P0.1)

   The ingestion logic should reuse the existing async HTTP and retry patterns (e.g., the `tenacity` strategy used in `ProviderDownloader._fetch`).

4. Persist raw artifacts locally under `data/raw/news/` and `data/raw/macro/events/` using a deterministic partitioning scheme (at minimum by `vendor/YYYY/MM/DD/`). Optionally mirror to S3 with a distinct prefix to avoid mixing market raw and macro/news raw.

5. Add tests for:

   - UTC normalization correctness
   - rejecting “forward-looking timestamps” relative to an ingestion run time
   - guaranteeing “no interpretation” by asserting the persisted schema does not include forbidden keys

## Concrete Steps

All commands below assume the repository root as the working directory.

1. Environment bootstrap:

   - `make setup`

2. Add configuration templates:

   - Create `config/secrets/news_api.json.example`.
   - Create `config/vendors/macro_feeds.json`.

3. Add schema artifact:

   - Create `docs/infra/phase0/schemas/macro_news_ingestion.yaml`.

4. Implement ingestion modules and CLI commands:

   - In `src/qf_downloader/cli.py`, add commands such as:

     - `ingest_news_backfill(vendor_name: str, start: str, end: str, ...)`
     - `ingest_macro_events_backfill(vendor_name: str, start: str, end: str, ...)`

   - Reuse `DownloadDB` for dedupe and last-successful tracking and write to the same metadata ledger pattern as P0.1.

5. Add tests:

   - Create `tests/unit/test_macro_news_ingestion_contract.py`.
   - Run `make test SUITE=unit`.

Expected (illustrative) transcript once tests exist:

    [pytest] APP_ENV=production uv run --dev -- python -m pytest tests/unit
    ...
    8 passed in 0.98s

## Validation and Acceptance

Acceptance is met when:

- No forward-looking timestamps:

  - The ingestion code rejects or flags any record whose timestamp is after the ingestion run time (with a clear policy: drop + record in metadata, or quarantine to a separate folder).

- No implicit event labeling:

  - Persisted macro events contain only raw vendor-provided fields and mechanical normalization fields (e.g., `timestamp_utc`, `vendor`, `source_id`).
  - No computed fields like `label`, `impact_score`, or `sentiment` exist.

- Event timestamps auditable:

  - The metadata ledger records the source timestamp field name, the source timezone (if any), and the normalized UTC timestamp.

Validation commands:

- `make test SUITE=unit`
- Optional integration (LocalStack): `APP_ENV=localstack make test SUITE=integration RUNTIME=docker`

## Idempotence and Recovery

- Ingestion commands must be safe to re-run for the same window:

  - Deduplicate by stable record IDs (if vendor provides them) or by checksum of raw payloads, and record “skipped” events in metadata.

- On partial failure:

  - Persisted artifacts must be atomic (write temp → rename) or explicitly marked partial.
  - The next run must resume from the last successful time boundary using `DownloadDB.get_last_successful` or the metadata ledger.

## Artifacts and Notes

Expected new or updated artifacts after implementation:

- `config/secrets/news_api.json.example`
- `config/vendors/macro_feeds.json`
- `docs/infra/phase0/schemas/macro_news_ingestion.yaml`
- `data/raw/news/` (directory)
- `data/raw/macro/events/` (directory)
- Potential shared modules with P0.1:

  - `src/qf_downloader/timestamp_normalization.py`
  - `src/qf_downloader/metadata_ledger.py`

- Unit tests under `tests/unit/`

## Interfaces and Dependencies

Internal interfaces to reuse:

- `DownloadDB` in `src/qf_downloader/db.py` for dedupe and last-successful markers.
- `S3Client` and `S3Indexer` for optional remote storage and indexing.

External dependencies:

- Quant rules: `docs/quant/return_calculation.yaml` (timezone conventions and alignment assumptions).
- Quant-approved macro provider list: `docs/quant/data_providers/macro_event_providers.yaml`.
- Vendor + auth config (Phase 0): `config/vendors/macro_feeds.json` and `config/secrets/news_api.json`.

Task dependencies:

- Hard dependency: Q0.1 timezone and alignment conventions (already present in `docs/quant/return_calculation.yaml`).
- Conceptual downstream dependency: Q0.7 macro event attribution will consume these raw artifacts; therefore this task must preserve provenance and avoid interpretive transformations.

- Open dependency (explicit): Quant (or the LLM team with Quant sign-off) must provide an approved list of “news text” sources if news ingestion is to be enforced as a binding input contract in the same way macro events are.
