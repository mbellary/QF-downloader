# Q0.8 — Microstructure Target Definitions (normative spec + contracts)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, microstructure prediction targets (order-flow imbalance, liquidity shocks, spread expansion, short-horizon impact) are defined in a way that is tick-aligned, causally valid, and isolated to horizons ≤ 5 minutes. The observable outcome is a Quant-owned normative spec (`docs/quant/microstructure.md` + `docs/quant/microstructure.yaml`), a schema registry entry under `docs/quant/target_schemas/`, and a downstream contract for derived artifacts under `targets/`.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.8.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/6
- [x] (2026-01-02 00:00Z) Created Quant-owned normative spec: `docs/quant/microstructure.md`.
- [x] (2026-01-02 00:00Z) Created Quant-owned normative schema: `docs/quant/microstructure.yaml`.
- [x] (2026-01-02 00:00Z) Created schema registry entry: `docs/quant/target_schemas/microstructure.yaml` and `docs/quant/target_schemas/microstructure.md`.
- [x] (2026-01-02 00:00Z) Ensured target classes, OFI definition, thresholding guidance, and horizon constraints are explicit.
- [x] (2026-01-02 00:00Z) Ensured derived artifact contracts are specified, including `targets/microstructure_schema.json`.

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/microstructure.md](../../docs/quant/microstructure.md), [docs/quant/microstructure.yaml](../../docs/quant/microstructure.yaml), [docs/quant/target_schemas/microstructure.yaml](../../docs/quant/target_schemas/microstructure.yaml), [targets/microstructure_schema.json](../../targets/microstructure_schema.json).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #6 for Q0.8).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Treat “horizon isolation (≤ 5 minutes)” and “no future ticks” as hard constraints encoded in both markdown and YAML.
  Rationale: The task’s acceptance criteria and deliverables explicitly require causal validity and horizon isolation.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The authoritative requirements are in `quant_tasks.md` under “Task Q0.8”. This task distinguishes:

- Quant-owned normative specs (under `docs/quant/`) that define target semantics.
- Derived artifacts (under `targets/`) generated downstream and required to conform exactly.
- A schema registry entry (under `docs/quant/target_schemas/`) defining required fields and causality rules.

## Task Spec Snapshot (from quant_tasks.md)

### Description

Defines prediction targets related to order-flow imbalance, liquidity shocks, and short-horizon price impact using tick-level and microstructure data.

### Objective

Provide well-defined targets for microstructure and order-flow ML models that are compatible with higher-level return and execution logic.

### Purpose

Define order-flow and liquidity-based prediction targets using tick-level and microstructure data.

### Business Use Cases

- Liquidity detection (avoid bad fills).
- Short-horizon trading.
- Execution timing.
- Stress detection.

### Data Providers

Data type required: tick data, order-flow proxies.

Approved providers: Dukascopy, TrueFX, LOBSTER (academic).

Relevance: targets must reflect actual order-flow behavior, not bar proxies.

### Example Data & Target

Example: aggressive_buy_vol 120 vs aggressive_sell_vol 40 yields order_flow_imbalance +80.

### Inputs

The task lists:

- Tick data: `/data/raw/fx/tick/` (DE)
- Order flow proxies: `/feature_store/micro/` (DE)
- Returns: `/data/clean/returns.parquet` (Quant)

### Target Classes

May include OFI, liquidity withdrawal events, short-horizon price impact, spread expansion events.

### OFI Definition (Example)

$OFI_t = \sum (\text{Aggressive Buy Volume} - \text{Aggressive Sell Volume})$, then threshold into positive/neutral/negative.

### Horizon Constraints

Microstructure horizons ≤ 5 minutes and must not overlap with directional horizons.

### Deliverables (Enhanced & Enforceable)

A. Normative specification artifacts (Quant-owned):

- `docs/quant/microstructure.yaml` MUST encode allowed target classes, tick alignment rules, OFI definition, thresholding logic, horizon constraints, forbidden overlap with directional targets, causal validity requirements (no future ticks).
- `docs/quant/microstructure.md` MUST explain economic interpretation, why bar proxies are insufficient, separation from directional signal, and limitations.

B. Derived artifact contracts (mandatory, downstream):

- `/targets/microstructure_targets.parquet` with timestamp, instrument, horizon, buy/sell volume, OFI, class, spread snapshot, liquidity state flag.
- `/targets/microstructure_schema.json` with schema_version, class definitions, horizon definitions, thresholds, tick aggregation rules, provenance, leakage checks.

C. Schema registry entry:

- `/docs/quant/target_schemas/microstructure.yaml`
- `/docs/quant/target_schemas/microstructure.md`

### Outputs

- `/targets/microstructure_targets.parquet`
- `/targets/microstructure_schema.json`
- `/docs/quant/target_schemas/microstructure.yaml`
- `/docs/quant/target_schemas/microstructure.md`

### Acceptance Criteria

- Targets derived only from past and current ticks.
- No dependence on future returns.
- Explicit horizon isolation.

## Plan of Work

Write the normative spec such that downstream derived artifacts cannot extend horizons, aggregate future ticks, or redefine OFI logic.

In `docs/quant/microstructure.md`, define each target class and, for each:

- Required inputs and alignment.
- Horizon restrictions.
- Thresholding and class mapping.
- Leakage and causality requirements.

In `docs/quant/microstructure.yaml`, encode the above with explicit enumerations and numeric parameters.

In `docs/quant/target_schemas/microstructure.yaml`, define the schema for the downstream parquet and metadata JSON.

## Concrete Steps

From the repository root:

1. Create `docs/quant/microstructure.md`.
2. Create `docs/quant/microstructure.yaml`.
3. Create `docs/quant/target_schemas/microstructure.yaml` and `docs/quant/target_schemas/microstructure.md`.
4. Optional validation:

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/microstructure.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- The spec is implementable from tick data and order-flow proxies.
- “No future ticks” and horizon constraints are explicit and enforceable.
- `docs/quant/microstructure.yaml` parses successfully.

## Idempotence and Recovery

Edits are safe and repeatable. Fix YAML syntax and retry parsing as needed.

## Artifacts and Notes

Expected artifacts (after implementation of this plan):

- `docs/quant/microstructure.md`
- `docs/quant/microstructure.yaml`
- `docs/quant/target_schemas/microstructure.yaml`
- `docs/quant/target_schemas/microstructure.md`

Derived artifacts (generated downstream, but contractually defined here):

- `/targets/microstructure_targets.parquet`
- `/targets/microstructure_schema.json`

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs temporally.

Interfaces to align with:

- Execution constraints (eventual `docs/quant/execution_constraints.yaml`) for spread/liquidity realism.
- Directional label horizons (eventual `docs/quant/alpha_dir.yaml`) to enforce non-overlap.

Task dependencies:

- None, temporally. Conceptual consistency only.
