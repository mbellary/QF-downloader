# Phase 0.2 — Macro & News Ingestion ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository uses ExecPlans as specified in PLANS.md at the repository root. This document must be maintained in accordance with PLANS.md.

## Purpose / Big Picture

After this change, a user can ingest raw macroeconomic events and raw news text into deterministic on-disk/S3 layouts with auditable provenance metadata, while explicitly binding timestamp conventions to Quant’s alignment contract (Q0.1) and provider allowlist contract (Q0.7).

A human can see it working by running the macro/news ingestion CLI for a fixed historical date range and verifying:

1) raw artifacts are written to the required storage prefixes (`/data/raw/macro/events/` and `/data/raw/news/`) without embedded interpretation (no sentiment, no scoring),

2) every artifact has a sidecar metadata JSON that is auditable (provider, request parameters, SHA-256 checksum, ingestion time, Quant contract hashes), and

3) rerunning the same ingest is idempotent (no duplicate artifacts in S3 or the on-disk layout; checksum ledger prevents double-writing).

## Task Statement (from data_tasks.md)

### Description

Define ingestion of exogenous macroeconomic and news data with no embedded interpretation or labeling.

### Objective

Provide clean, timestamped, alignment-ready macro inputs for later Quant-defined attribution (Q0.7).

### Inputs

- News API credentials (LLM Team): `config/secrets/news_api.json`
- Macro data vendor specs (LLM Team): `config/vendors/macro_feeds.json`
- Quant alignment rules (Quant Q0.1): `docs/quant/return_calculation.yaml`
- Approved data providers (Quant Q0.7): `docs/quant/data_providers/macro_event_providers.yaml`

### Deliverables

- Raw news ingestion
- Raw macro event ingestion
- Text normalization (no sentiment, no scoring)

### Outputs

- Raw news text: `data/raw/news/`
- Raw macro events: `data/raw/macro/events/`
- Macro News Ingestion schema: `docs/infra/phase0/schemas/macro_news_ingestion.yaml`
- Macro data provider config: `config/vendors/macro_providers.json`

### Acceptance Criteria

- No forward-looking timestamps
- No implicit event labeling
- Event timestamps auditable

## Progress

- [x] (2026-01-11) Environment verified on Linux: `make -f Makefile.test setup`, `make -f Makefile.test check`, and `make -f Makefile.test test SUITE=unit` pass.
- [x] (2026-01-11) Task branch created locally: `task/p0-2-macro-news-ingestion`.
- [x] (2026-01-11) ExecPlan created: `plans/p0_2_macro_news_ingestion/p0_2_macro_news_ingestion_execplan.md`.

- [x] (2026-01-11) GitHub tracking issue created for Phase 0.2: https://github.com/mbellary/QF-downloader/issues/17
- [x] (2026-01-11) Program Manager verification: Issue #17 is open and canonical; sync comment posted (see issue comments).
- [x] (2026-01-11) Design document created: `plans/p0_2_macro_news_ingestion/p0_2_macro_news_ingestion_design.md`
- [x] (2026-01-11) Provider spec contracts added: `config/vendors/macro_feeds.json` (raw endpoint specs) and `config/vendors/macro_providers.json` (curated allowlisted providers).
- [x] (2026-01-11) Secrets scaffolding added and git-safed: `config/secrets/news_api.json` (gitignored by pattern) with committed `config/secrets/news_api.example.json`.
- [x] (2026-01-11) Schema contract added: `docs/infra/phase0/schemas/macro_news_ingestion.yaml`.
- [x] (2026-01-11) Implementation added: `src/qf_downloader/exogenous_downloader.py` + metadata/CLI extensions for macro + news.
- [x] (2026-01-11) Unit tests added/updated for Phase 0.2 contracts (contract tests; execution pending until implementation lands): [tests/unit/test_p0_2_macro_news_ingestion.py](tests/unit/test_p0_2_macro_news_ingestion.py)
- [x] (2026-01-11) Integration tests added for LocalStack S3 contract (macro_events + news; skipped until implementation lands): [tests/integration/test_p0_2_macro_news_ingestion_integration.py](tests/integration/test_p0_2_macro_news_ingestion_integration.py)
- [x] (2026-01-11) Validation passes (unit): `make -f Makefile.test check` and `make -f Makefile.test test SUITE=unit`.
- [x] (2026-01-11) Validation passes (integration): `make -f Makefile.test test SUITE=integration RUNTIME=docker` (user-confirmed).
- [ ] (2026-01-11) Branch pushed: `task/p0-2-macro-news-ingestion`.
- [ ] (2026-01-11) PR opened against `main` (links Issue #17).

## Surprises & Discoveries

- Observation: Several Quant “.yaml” documents are JSON stored in a `.yaml` file (YAML 1.2 is a superset of JSON). This repo currently parses `docs/quant/return_calculation.yaml` via JSON for determinism in `src/qf_downloader/metadata.py`.
  Evidence: `src/qf_downloader/metadata.py:load_quant_return_spec` uses `json.loads` on the file contents.

- Observation: Legacy provider config at `src/qf_downloader/providers.yaml` already contains macro provider examples (`econdb`, `fmp`) but is deprecated in favor of `config/vendors/fx_providers.json` for Phase 0.1.
  Evidence: Header comment in `src/qf_downloader/providers.yaml`.

- Observation: The dev environment used by `make -f Makefile.test ...` currently runs on Python 3.14.x in this workspace.
  Evidence: `pytest` header during unit tests shows `platform linux -- Python 3.14.2`.

## Decision Log

- Decision: Implement Phase 0.2 ingestion by reusing existing primitives (S3 upload, SQLite checksum ledger, LocalStack support, failure recording) from Phase 0.1 instead of introducing a new ingestion framework.
  Rationale: `src/qf_downloader/downloader.py`, `src/qf_downloader/db.py`, `src/qf_downloader/storage.py`, and `src/qf_downloader/metadata.py` already implement idempotence, audit metadata patterns, and test harnesses; extending these reduces risk and keeps Phase 0 tasks consistent.
  Date/Author: 2026-01-11 / Copilot

- Decision: Treat “no forward-looking timestamps” as a data ingestion constraint (what date ranges we are allowed to ingest), not as an assumption that upstream providers never publish future-scheduled events.
  Rationale: Many macro calendars include scheduled future events; Phase 0.2 must ensure stored partitions are not forward-looking by default, so later phases cannot accidentally train on future information. This is enforced by defaulting to ingesting complete prior UTC days only, and by rejecting explicit requests for future date ranges.
  Date/Author: 2026-01-11 / Copilot

- Decision: Track Phase 0.2 implementation work via GitHub Issue #17.
  Rationale: Program Manager workflow requires Issue → Branch → PR traceability; this issue will remain the canonical artifact for Phase 0.2 execution.
  Date/Author: 2026-01-11 / Copilot (Issue: https://github.com/mbellary/QF-downloader/issues/17)

- Decision: Treat Issue #17 as the single canonical tracking issue for this ExecPlan; do not create duplicates.
  Rationale: Keeps all discussion and status in one place and avoids issue drift.
  Date/Author: 2026-01-11 / Program Manager

## Outcomes & Retrospective

- Initial planning complete: repository environment verified and Phase 0.2 ExecPlan drafted.
- Next: implement milestones with tests.

## Context and Orientation

This repository is a Python package (see `pyproject.toml`) that currently ingests raw FX market data (Phase 0.1) by fetching provider endpoints, writing raw bytes to deterministic on-disk paths, uploading the same bytes to S3, and writing sidecar metadata that binds ingestion to Quant Q0.1 time conventions.

Key modules to reuse and/or extend:

- `src/qf_downloader/cli.py`: Typer CLI. It currently supports `list-providers`, `run` (polling), and `backfill` for provider configs.
- `src/qf_downloader/provider_config.py`: loads provider configuration from JSON/YAML into a normalized dict shape.
- `src/qf_downloader/downloader.py`: `ProviderDownloader` fetches a daily artifact, deduplicates via `DownloadDB`, uploads to S3, writes sidecar metadata, and indexes in DynamoDB.
- `src/qf_downloader/metadata.py`: builds sidecar metadata and maintains the rollup manifest at `pipelines/ingestion/fx/metadata.json`.
- `src/qf_downloader/db.py`: SQLite checksum ledger and failure tracking.
- `docs/quant/return_calculation.yaml`: Quant Q0.1 alignment contract. Phase 0.2 must bind ingestion metadata to this file (hash + effective_date), the same way Phase 0.1 does.
- `docs/quant/data_providers/macro_event_providers.yaml`: Quant Q0.7 allowlist of macro providers; Phase 0.2 must not ingest from providers outside this allowlist unless explicitly documented as “disabled / not approved”.

Definitions used in this plan:

- “Raw macro event”: the exact vendor-provided payload describing macroeconomic events and their timestamps (scheduled time, actual release time if present, revisions if present). Phase 0.2 stores these payloads without labeling or scoring.
- “Raw news”: the exact vendor-provided payload containing news headlines/articles or transcript text. Phase 0.2 may perform only mechanical normalization (UTF-8 decoding, whitespace normalization), and must not add sentiment, entity labels, or event categories.
- “Sidecar metadata”: a JSON file stored alongside each raw artifact describing provenance (provider, request parameters, checksum), ingestion time, and Quant contract hashes.

## Plan of Work

This section describes how to implement Task 0.2 strictly within Phase 0 rules (no labels, no modeling logic). Milestones are independently verifiable.

Implementation must follow the design in `plans/p0_2_macro_news_ingestion/p0_2_macro_news_ingestion_design.md`.

### Milestone 1 — Add Phase 0.2 configuration contracts under `config/`

At the end of this milestone, the repository has explicit vendor and secrets configuration locations matching the Task 0.2 statement.

Work:

- Add provider endpoint specs: create `config/vendors/macro_feeds.json`.

  - This file defines the raw upstream endpoints and request shapes for macro and news providers.
  - It must follow the same high-level shape as other provider config files: a JSON object with a top-level `providers` list, compatible with `src/qf_downloader/provider_config.py:load_providers_config`.

- Add curated provider allowlist mapping: create `config/vendors/macro_providers.json`.

  - This file is the “Phase 0.2 contract view” of providers and must be aligned with `docs/quant/data_providers/macro_event_providers.yaml`.
  - Providers not in the Quant allowlist must be marked `enabled=false` and documented as “not Quant-approved”.

- Add secrets scaffolding:

  - Create `config/secrets/news_api.example.json` (committed) and `config/secrets/news_api.json` (gitignored).
  - Update `config/secrets/README.md` and `.gitignore` if needed so secrets cannot be committed.

- Extend `src/qf_downloader/config.py` to support Phase 0.2 configuration paths, without breaking Phase 0.1 defaults.

  - Add `MACRO_PROVIDERS_FILE` and `NEWS_PROVIDERS_FILE` (or a single `EXOGENOUS_PROVIDERS_FILE`) with safe defaults under `config/vendors/`.
  - Keep `PROVIDERS_FILE` behavior for Phase 0.1 intact.

### Milestone 2 — Deterministic storage layout for macro events and news

At the end of this milestone, Phase 0.2 outputs exist exactly at the paths required by the task statement.

Work:

- Define deterministic on-disk prefixes derived only from provider name, data type, and date partition:

  - Macro events: `data/raw/macro/events/<provider>/<YYYY>/<MM>/<DD>/...`
  - News: `data/raw/news/<provider>/<YYYY>/<MM>/<DD>/...`

- Adopt a deterministic filename rule. One safe default (example, not required):

  - Macro events: `macro_events_<YYYYMMDD>.json` (or `.ndjson` if streaming)
  - News: `news_<YYYYMMDD>.json` (or `.ndjson`)

- Ensure that for each raw artifact, a sidecar metadata file is written next to it:

  - `.../<filename>.metadata.json`

### Milestone 3 — Implement macro + news ingestion with auditable metadata and idempotence

At the end of this milestone, a user can run CLI commands to ingest macro events and news for a historical date range, and rerun them safely with no duplicates.

Work:

- Introduce a Phase 0.2 ingestion module that can ingest providers that are not “FX pair/day” shaped.

  - Preferred approach: add a new module, e.g. `src/qf_downloader/exogenous_downloader.py`, containing an `ExogenousProviderDownloader` that:

    - accepts a provider config dict from `load_providers_config`
    - fetches the provider response bytes using `aiohttp` + `tenacity`
    - writes raw bytes to the deterministic paths (Milestone 2)
    - uploads to S3 using `src/qf_downloader/storage.py:S3Client`
    - deduplicates using `src/qf_downloader/db.py:DownloadDB` with a stable provider scope key, e.g. `<provider>#<artifact_type>#<YYYYMMDD>`

- Extend metadata generation:

  - Add a new schema contract file: `docs/infra/phase0/schemas/macro_news_ingestion.yaml`.
  - Extend `src/qf_downloader/metadata.py` to support a second schema_id for Phase 0.2, e.g. `infra.phase0.macro_news_ingestion`.
  - Sidecar metadata must include:

    - provider name
    - artifact type: `macro_events` vs `news`
    - request URL (and redacted headers)
    - request date window (start/end) used for ingestion
    - hashes: SHA-256 of raw bytes
    - time contract: UTC binding + Quant spec hash/effective_date from `docs/quant/return_calculation.yaml`

- Implement a rollup manifest (recommended for audit symmetry with Phase 0.1):

  - Create or update `pipelines/ingestion/macro_news/metadata.json` similarly to `pipelines/ingestion/fx/metadata.json`.

- Failure recording:

  - Reuse `DownloadDB.record_failure` and `DownloadDB.clear_failure` patterns from Phase 0.1 for each partitioned macro/news artifact.

### Milestone 4 — Text normalization (mechanical only)

At the end of this milestone, raw news can be consumed downstream without encoding instability, but without any interpretation.

Work:

- Define “text normalization” narrowly to avoid violating Phase 0 rules:

  - Ensure payloads are UTF-8 decodable (replace invalid byte sequences deterministically).
  - Normalize newlines to `\n` and trim NUL/control characters.
  - Do not compute sentiment, relevance, topic classification, entity extraction, event labels, or scores.

- If normalization changes content, store both:

  - the original raw vendor bytes (`news_<date>.raw`) and
  - the normalized JSON/NDJSON representation (`news_<date>.json`).

### Milestone 5 — CLI + tests + acceptance

At the end of this milestone, Phase 0.2 can be exercised end-to-end with unit tests (and optionally LocalStack integration tests).

Work:

- Extend `src/qf_downloader/cli.py` with Phase 0.2 commands. One workable shape:

  - `macro-backfill --provider-name <name> --start YYYY-MM-DD --end YYYY-MM-DD`
  - `news-backfill --provider-name <name> --start YYYY-MM-DD --end YYYY-MM-DD`

- Enforce “no forward-looking timestamps” by default:

  - default ingestion window must end at the last fully completed UTC day
  - if a user specifies an end date beyond `datetime.now(UTC).date() - 1`, reject with a clear error

- Add unit tests under `tests/unit/` for:

  - deterministic path construction
  - sidecar metadata contains Quant spec hash and UTC conventions
  - idempotence (second run is skipped due to checksum ledger)
  - forward-looking date range rejection

- If S3/DynamoDB indexing is used for macro/news, add integration tests under `tests/integration/` following the Phase 0.1 pattern.

## Concrete Steps

All commands below assume repo root:

    cd /home/mbellary/wsl/projects/QF-downloader

Environment setup:

    make -f Makefile.test setup

Lint/format and tests:

0) Read the design document:

  - `plans/p0_2_macro_news_ingestion/p0_2_macro_news_ingestion_design.md`

    make -f Makefile.test check
    make -f Makefile.test test SUITE=unit

Example usage (to be implemented by this plan):

    uv run --dev -- python -m qf_downloader.cli list-providers --providers-file config/vendors/macro_feeds.json

    uv run --dev -- python -m qf_downloader.cli macro-backfill --provider-name fred --start 2025-01-01 --end 2025-01-10

    uv run --dev -- python -m qf_downloader.cli news-backfill --provider-name <news_vendor> --start 2025-01-01 --end 2025-01-10

Expected outputs after a successful run (example paths):

    data/raw/macro/events/fred/2025/01/10/macro_events_20250110.json
    data/raw/macro/events/fred/2025/01/10/macro_events_20250110.json.metadata.json

    data/raw/news/<news_vendor>/2025/01/10/news_20250110.json
    data/raw/news/<news_vendor>/2025/01/10/news_20250110.json.metadata.json

## Validation and Acceptance

Acceptance should be phrased as behavior a human can verify:

- Running the Phase 0.2 ingestion commands for a historical range writes raw artifacts to `data/raw/macro/events/` and `data/raw/news/` and uploads the same bytes to S3.
- Each artifact has a sidecar metadata file that:

  - references `docs/quant/return_calculation.yaml` and includes its SHA-256,
  - records ingestion time in UTC, and
  - redacts secrets.

- Rerunning the same ingestion is idempotent:

  - local files are unchanged
  - S3 keys are unchanged
  - the checksum ledger causes “skipped” results rather than duplicates

- Forward-looking date ranges are rejected by default (clear error message).

- Tests:

  - `make -f Makefile.test test SUITE=unit` passes
  - any new tests for Phase 0.2 fail before the implementation and pass after.

## Idempotence and Recovery

- Idempotence must be guaranteed by the checksum ledger in `src/qf_downloader/db.py:DownloadDB`.
- If a provider call fails (timeout/5xx/4xx), the failure must be recorded (reusing Phase 0.1 `fetch_failures` table) and should be retryable without manual cleanup.
- If a partial local file is written, the ingest rerun must overwrite it deterministically only when the checksum differs (or write to a temp file and move into place atomically).

## Artifacts and Notes

Important repo contracts to preserve:

- Secrets must never be committed. Keep `config/secrets/*.json` ignored, and commit only `*.example.json` templates.
- Provider specs must be deterministic JSON contracts under `config/vendors/`.
- Schema contract must be added at `docs/infra/phase0/schemas/macro_news_ingestion.yaml`.

## Interfaces and Dependencies

Required libraries and services (already present in this repo):

- `aiohttp` for HTTP fetches
- `tenacity` for retries
- `aiosqlite` for checksum ledger and failure persistence (`src/qf_downloader/db.py`)
- `aioboto3`/S3 via `src/qf_downloader/storage.py:S3Client`
- Optional DynamoDB indexing via `src/qf_downloader/s3_indexer.py:S3Indexer`

Prescribed interfaces to add (names and paths are part of the contract of this plan):

- In `src/qf_downloader/exogenous_downloader.py`, define:

    class ExogenousProviderDownloader:
        def __init__(self, provider: dict[str, object], s3: S3Client, db: DownloadDB, base_data_dir: str = "./data") -> None:
            ...

        async def ingest_day(self, day_utc: datetime, *, artifact_type: str) -> dict[str, object]:
            """Ingest a single UTC day partition and return a structured result."""

        async def backfill_range(self, start_utc: datetime, end_utc: datetime, *, artifact_type: str) -> None:
            ...

- In `src/qf_downloader/metadata.py`, extend sidecar generation so Phase 0.2 can emit `schema_id="infra.phase0.macro_news_ingestion"` with:

  - quant contract hash (Q0.1)
  - provider allowlist reference (Q0.7 path)
  - UTC binding

If you revise this plan, ensure the changes are reflected across all sections (especially `Progress`, `Decision Log`, and `Concrete Steps`), and add a short note at the end of this file describing what changed and why.
