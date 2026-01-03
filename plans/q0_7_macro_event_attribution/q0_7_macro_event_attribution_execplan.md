# Q0.7 — Macro Event Return Attribution Rules (normative spec + contracts)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, returns can be attributed to macroeconomic events in a reproducible, auditable way using explicit event windows, baseline return definitions, and optional volatility normalization. The observable outcome is a Quant-owned normative spec (`docs/quant/macro_event.md` + `docs/quant/macro_event.yaml`), a schema registry entry (`docs/quant/target_schemas/macro_event.yaml` + `.md`), and a downstream contract for derived artifacts under `targets/`.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.7.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/5
- [x] (2026-01-02 00:00Z) Created Quant-owned normative spec: `docs/quant/macro_event.md`.
- [x] (2026-01-02 00:00Z) Created Quant-owned normative schema: `docs/quant/macro_event.yaml`.
- [x] (2026-01-02 00:00Z) Created schema registry entry: `docs/quant/target_schemas/macro_event.yaml` and `docs/quant/target_schemas/macro_event.md`.
- [x] (2026-01-02 00:00Z) Ensured event windows, abnormal return, delayed reaction, and overlap policy are explicit.
- [x] (2026-01-02 00:00Z) Ensured derived artifact contracts are specified, including `targets/macro_event_metadata.json`.

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/macro_event.md](../../docs/quant/macro_event.md), [docs/quant/macro_event.yaml](../../docs/quant/macro_event.yaml), [docs/quant/target_schemas/macro_event.yaml](../../docs/quant/target_schemas/macro_event.yaml), [targets/macro_event_metadata.json](../../targets/macro_event_metadata.json).

## Surprises & Discoveries

- Observation: The task explicitly lists Inputs referencing Q0.1 and Q0.2/Q0.12, which conflicts with the global “Q0 tasks are co-equal and do not depend temporally” rule.
  Evidence: Task Q0.7 Inputs table in `quant_tasks.md`.

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #5 for Q0.7).

## Decision Log

- Decision: Preserve the Inputs section as written, but treat it as conceptual alignment rather than a temporal dependency.
  Rationale: The plan must include every section described in the task while respecting the Q0 co-equal rule.
  Date/Author: 2026-01-02 / Copilot

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The authoritative requirements are in `quant_tasks.md` under “Task Q0.7”. The task defines macro-event attribution as a combination of:

- Exogenous event timestamps/classes from official sources.
- A deterministic mapping from each event to a pre/post window on market data.
- An “abnormal return” definition that subtracts a baseline expected return.
- Optional normalization by pre-event volatility.

The task also separates Quant-owned normative specs (in `docs/quant/`) from derived artifacts that must be generated downstream (in `targets/`).

## Task Spec Snapshot (from quant_tasks.md)

### Description

Specifies how returns are attributed to macroeconomic events using event windows, abnormal return definitions, and volatility-adjusted reactions.

### Objective

Enable reliable modeling of market reactions to macro events, separating structural moves from noise and background volatility.

### Purpose

Define how market reactions to macroeconomic events are measured, isolated, and normalized.

### Business Use Cases

- Event risk control.
- News-aware trading.
- Volatility forecasting (events drive σ regimes).
- Post-event drift analysis.

### Data Providers

Data type required: event timestamps, market reactions, baseline volatility.

Approved providers: FRED, ECB calendars, Trading Economics (free metadata).

Relevance: attribution must use official, auditable event sources.

### Example Data & Target

Example: CPI event where post-event return is +0.8% vs baseline +0.1% gives abnormal return +0.7%.

### Inputs

The task lists:

- Return calculation rules: `/docs/quant/return_calculation.yaml` (Quant Q0.1)
- Baseline return definition: `/docs/quant/backtest_rules.yaml` (Quant Q0.2 / Q0.12)
- Event window definitions: “This document”

### Global System Constraints

Must comply with volatility normalization rules and the noise-vs-signal separation doctrine.

### Event Window Definition

Each event $E$ has a pre-event window $[T_E - \Delta_{pre}, T_E]$ and post-event window $[T_E, T_E + \Delta_{post}]$, with window sizes depending on event class.

### Abnormal Return Calculation

Abnormal return $AR_E = R_{post} - \mathbb{E}[R \mid \text{baseline}]$, with optional normalization $AR_E^{norm} = AR_E / \sigma_{pre}$.

### Delayed Reaction Handling

Allow multi-bar reaction windows, record peak reaction time, and store reaction decay metrics.

### Deliverables (Enhanced & Enforceable)

A. Normative specification artifacts (Quant-owned):

- `docs/quant/macro_event.yaml` MUST encode event classes, timestamp alignment rules, window definitions, baseline return proxy, abnormal return formula, optional normalization, delayed reaction handling, overlap/exclusion rules.
- `docs/quant/macro_event.md` MUST describe economic rationale, structural vs noise reactions, relationship to volatility/regimes, and limitations/failure modes.

B. Derived artifact contracts (mandatory, downstream):

- `/targets/macro_event_returns.csv` with event_id/type/timestamp, pre/post window returns, abnormal and normalized abnormal returns, peak reaction timestamp, decay metric.
- `/targets/macro_event_metadata.json` with schema version, class definitions, window sizes, baseline methodology reference, volatility source, overlap policy, provenance.

C. Schema registry entry:

- `/docs/quant/target_schemas/macro_event.yaml`
- `/docs/quant/target_schemas/macro_event.md`

### Outputs

- `/targets/macro_event_returns.csv`
- `/targets/macro_event_metadata.json`
- `/docs/quant/target_schemas/macro_event.yaml`
- `/docs/quant/target_schemas/macro_event.md`

### Acceptance Criteria

- No overlap between events.
- Clear baseline definition.
- Both raw and volatility-normalized abnormal returns stored.
- Auditable event-to-return mapping.

## Plan of Work

Write the normative spec and schema so that downstream teams can generate the derived artifacts without redefining windows, baseline logic, or normalization.

In `docs/quant/macro_event.md`, define:

- Event classes and how events are identified.
- Window sizes per class and overlap rules.
- Baseline return definition and how it is computed.
- Abnormal return and optional normalization formulas.
- Delayed reaction window handling and required metadata fields.

In `docs/quant/macro_event.yaml`, encode the above as machine-readable configuration.

In `docs/quant/target_schemas/macro_event.yaml`, define the exact schema for the derived CSV/JSON artifacts.

## Concrete Steps

From the repository root:

1. Create `docs/quant/macro_event.md`.
2. Create `docs/quant/macro_event.yaml`.
3. Create `docs/quant/target_schemas/macro_event.yaml` and `docs/quant/target_schemas/macro_event.md`.
4. Optional validation:

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/macro_event.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- The normative spec prevents downstream redefinition of windows, baseline, and normalization.
- Overlap/exclusion rules are explicit.
- `docs/quant/macro_event.yaml` parses successfully.

## Idempotence and Recovery

Edits are safe and repeatable. Fix YAML syntax and retry parsing as needed.

## Artifacts and Notes

Expected artifacts (after implementation of this plan):

- `docs/quant/macro_event.md`
- `docs/quant/macro_event.yaml`
- `docs/quant/target_schemas/macro_event.yaml`
- `docs/quant/target_schemas/macro_event.md`

Derived artifacts (generated downstream, but contractually defined here):

- `/targets/macro_event_returns.csv`
- `/targets/macro_event_metadata.json`

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs temporally.

Interfaces to align with:

- Canonical return calculation (eventual `docs/quant/return_calculation.yaml`).
- Backtest rules / baseline definitions (eventual `docs/quant/backtest_rules.yaml`).
- System KPI doctrine (eventual `docs/quant/system_kpis.yaml`) if event-conditional KPIs are used.

Task dependencies:

- None, temporally. Conceptual consistency only.
