# Q0.10 — Feature Intent & Constraints Specification (normative spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, feature engineering is governed by an explicit, quant-owned intent taxonomy plus enforceable temporal and usage constraints. The observable outcome is that the repo contains:

- `docs/quant/feature_intent_and_constraints.md` (human-readable intent + governance spec)
- `docs/quant/feature_constraints.json` (machine-readable constraint schema)

Downstream feature code can be audited against these artifacts, and leakage/hindsight bias/regime confusion are explicitly prohibited.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.10.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/10
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/feature_intent_and_constraints.md`.
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/feature_constraints.json`.
- [x] (2026-01-02 00:00Z) Ensured the spec includes guiding principle, scope, intent taxonomy, temporal constraints, usage constraints, leakage rules, and documentation requirements.
- [x] (2026-01-02 00:00Z) Validated JSON parses.

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/feature_intent_and_constraints.md](../../docs/quant/feature_intent_and_constraints.md), [docs/quant/feature_constraints.json](../../docs/quant/feature_constraints.json).

## Surprises & Discoveries

- Observation: The Q0 “structural rule” says tasks do not consume outputs of other Q0 tasks, but this task includes an extensive Inputs table referencing multiple `targets/` artifacts and other Q0 documents.
  Evidence: Task Q0.10 Inputs table in `quant_tasks.md`.

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #10 for Q0.10).

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Use JSON (not YAML) as the canonical machine-readable format for feature constraints.
  Rationale: The quant spec explicitly calls for `feature_constraints.json`; JSON is also easy to validate and consume across stacks.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quant requirements for this task are in `quant_tasks.md` under “Task Q0.10”. Q0 tasks are declarative and co-equal.

This task produces:

- `docs/quant/feature_intent_and_constraints.md`
- `docs/quant/feature_constraints.json`

The quantitative spec lists `docs/quant/feature_constraints.json` as a global constraint artifact. This task is therefore the source of that “constitutional” document.

## Task Spec Snapshot (from quant_tasks.md)

### Purpose

Define the economic intent, permissible information content, temporal constraints, and usage boundaries for all features used in the forecasting engine, ensuring feature engineering serves the noise-aware objective and does not introduce leakage, regime confusion, or spurious signal amplification.

### Guiding Principle

Features exist to help separate signal from noise, explain volatility and regimes, and only then support return prediction.

### Scope

This spec defines what information a feature may encode, where it may be used in the decision stack, and what it must not do. It does not define formulas, indicators, implementation logic, or selection/ranking.

### Business Use Cases

- Governance: auditability of feature choices.
- Leakage prevention: keep ML honest.
- Cross-team consistency: shared rules for what features are allowed.

### Data Providers

Data types required: upstream targets, macro context, execution constraints. Approved providers: inherits all above providers.

### Inputs

The task lists an explicit Inputs table (treat as conceptual alignment, not temporal dependency). Examples include:

- Return calculation rules: `/docs/quant/return_calculation.md`
- Directional label artifacts: `/targets/alpha_dir_labels.csv`, `/targets/alpha_dir_label_metadata.json`, `/docs/quant/target_schemas/alpha_dir.yaml`
- Macro-event artifacts: `/targets/macro_event_returns.csv`, `/targets/macro_event_metadata.json`, `/docs/quant/target_schemas/macro_event.yaml`
- Microstructure artifacts: `/targets/microstructure_targets.parquet`, `/targets/microstructure_schema.json`, `/docs/quant/target_schemas/microstructure.yaml`
- Path outcome artifacts: `/targets/path_outcomes.parquet`, `/targets/path_label_metadata.json`, `/docs/quant/target_schemas/path_outcomes.yaml`
- Execution constraints: `/docs/quant/execution_constraints.yaml`
- Noise-aware system objective: `/docs/quant/system_kpis.yaml`

### Global System Constraints

This task defines part of the global system constraints and is itself authoritative.

### Feature Intent Taxonomy

All features must map to exactly one primary intent category. The task defines categories:

- Signal (α) features
- Noise (ε) features
- Volatility (σ) features
- Regime features
- Macro & exogenous features

Each category has intent, examples, and constraints (e.g., α features must not be used without gating).

### Temporal Constraints

All features must declare lookback horizon, update frequency, alignment, and latency tolerance.

### Usage Constraints

Each feature must declare allowed usage areas (directional prediction conditional; volatility/regime allowed; execution logic disallowed, etc.).

### Information Leakage Rules

Explicitly prohibited: future returns/prices, realized P&L, post-trade info, and construction that depends on target outcomes. Features must be causally valid at inference.

### Feature Documentation Requirements

Every feature must include metadata fields: name, intent category, rationale, horizon alignment, usage permissions, leakage assessment.

### Deliverables

- `docs/quant/feature_intent_and_constraints.md` (feature intent specification)
- `docs/quant/feature_constraints.json` (feature constraint schema)

### Outputs

- `docs/quant/feature_intent_and_constraints.md`
- `docs/quant/feature_constraints.json`

### Acceptance Criteria

Feature engineering cannot proceed without mapping each feature to an approved intent and passing leakage constraints.

## Plan of Work

Write `docs/quant/feature_intent_and_constraints.md` as a governance document with the exact sections from the task: guiding principle, scope, taxonomy, temporal constraints, usage constraints, leakage rules, and documentation requirements.

Write `docs/quant/feature_constraints.json` as the machine-readable representation of:

- intent categories (stable IDs)
- allowed usage areas per category
- prohibited information patterns
- required metadata fields

The JSON must be suitable for automated checks (e.g., rejecting a feature without intent mapping).

## Concrete Steps

From the repository root:

1. Create `docs/quant/feature_intent_and_constraints.md`.
2. Create `docs/quant/feature_constraints.json`.
3. Validate JSON parses (recommended):

   - `python -c "import json, pathlib; json.loads(pathlib.Path('docs/quant/feature_constraints.json').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- Intent categories and prohibited patterns are explicit and enforceable.
- JSON parses and contains all constraints needed for automated checks.

## Idempotence and Recovery

Edits are safe and repeatable. If JSON parsing fails, fix syntax and retry.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/feature_intent_and_constraints.md`
- `docs/quant/feature_constraints.json`

Illustrative JSON structure (example only):

    {
      "intents": {
        "volatility": {"description": "Features intended to predict σ"}
      },
      "prohibited": ["future_return", "label_proxy"]
    }

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Interfaces it must align with:

- Loss constraints (eventual `docs/quant/loss_constraints.yaml`) so objectives and features stay consistent.
- System KPIs (eventual `docs/quant/system_kpis.yaml`) so optimization is aligned with intent.

Task dependencies:

- None, temporally. Conceptual alignment only.
