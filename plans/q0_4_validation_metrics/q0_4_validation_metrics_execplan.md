# Q0.4 — Validation Metrics (spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, model evaluation and promotion decisions are driven by a uniform, quant-approved metric set that is explicitly regime-aware and noise-first. The observable outcome is that `docs/quant/validation_metrics.md` and `docs/quant/validation_metrics.yaml` exist, define each metric (including formula and interpretation), and give guidance on what constitutes “better” vs “worse” without ad-hoc interpretation.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.4.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/1
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/validation_metrics.md` with definitions, formulas, and interpretation.
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/validation_metrics.yaml` mirroring the markdown.
- [x] (2026-01-02 00:00Z) Added regime-aware guidance and ensured consistency with noise-first metric hierarchy.
- [x] (2026-01-02 00:00Z) Validated schema parses (JSON-as-YAML).

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/validation_metrics.md](../../docs/quant/validation_metrics.md), [docs/quant/validation_metrics.yaml](../../docs/quant/validation_metrics.yaml).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #1 for Q0.4).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Require every metric to state (a) definition, (b) measurement window, (c) optimization direction, and (d) failure modes.
  Rationale: Prevents “metric theater” and ensures consistent governance.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quant requirements for this task are in `quant_tasks.md` under “Task Q0.4”. Q0 tasks are declarative and co-equal; this metric specification must not depend on other Q0 outputs.

This task produces:

- `docs/quant/validation_metrics.md`
- `docs/quant/validation_metrics.yaml`

These metrics are intended to be referenced by:

- System-level KPI gates (Q0.11).
- Loss constraints (Q0.12).
- Model selection and research reporting.

## Task Spec Snapshot (from quant_tasks.md)

### Description

Enumerates quantitative metrics used to evaluate model performance, strategy robustness, and risk-adjusted returns across regimes.

### Objective

Create a uniform evaluation standard so model selection, promotion, and rejection are driven by consistent, quant-approved criteria.

### Business Use Cases

- Model promotion: decide what goes to prod.
- Risk-adjusted review: returns alone are misleading.
- Regime stress testing: models must survive regime shifts.
- Governance: transparent, auditable metrics.

### Data Providers

Data type required:

- Returns
- Volatility estimates
- Regime segments

Approved providers (examples): Stooq, FRED, Alpha Vantage.

Relevance: metrics must survive macro regime shifts, not just local samples.

### Inputs

None (pure quant research specification).

### Deliverables

- `validation_metrics.md` describing:
  - Sharpe
  - Sortino
  - Max Drawdown
  - PBO (Probability of Backtest Overfitting)
  - SNR (Signal-to-Noise Ratio)
  - Hit ratio
  - Regime-aware returns
- `validation_metrics.yaml` encoding the same.

### Outputs

- `docs/quant/validation_metrics.md`
- `docs/quant/validation_metrics.yaml`

## Plan of Work

Write a metric catalog where each metric entry contains:

- Name and identifier (stable key for code).
- Exact mathematical definition.
- Required inputs (series, regimes, horizons).
- Measurement rules (windowing, annualization, handling missing data).
- Interpretation: what “good” means and what can cause false positives.

Ensure regime-awareness is first-class:

- Define how a “regime” is represented (a categorical label per timestamp).
- Define how to compute metrics per-regime and how to aggregate (worst-case, weighted average, etc.).

Represent the catalog in YAML with stable identifiers so dashboards and CI gates can reference metrics by key.

## Concrete Steps

From the repository root:

1. Create `docs/quant/validation_metrics.md` with one section per metric. For each:

   - Provide formula and definition.
   - Define required data inputs and frequency.
   - Define regime-aware computation.

2. Create `docs/quant/validation_metrics.yaml` with a list/map of metric definitions:

   - Include `id`, `name`, `direction` (higher/lower better), `inputs`, and `formula_text`.

3. Validate YAML parses (optional):

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/validation_metrics.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- A reader can compute any listed metric from the definition without assumptions.
- Regime-aware variants are explicitly defined (not hand-waved).
- YAML parses and can be referenced programmatically by stable metric IDs.

## Idempotence and Recovery

Edits are safe and repeatable. If YAML parsing fails, fix syntax and retry.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/validation_metrics.md`
- `docs/quant/validation_metrics.yaml`

Illustrative YAML entry (example only):

    metrics:
      sharpe:
        direction: "higher_is_better"
        inputs: ["return_series"]
        annualization: "sqrt(252)"

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Interfaces it must align with:

- System KPI gates (eventual artifact `docs/quant/system_kpis.yaml`) should reference metric IDs defined here.
- Loss constraints (eventual artifact `docs/quant/loss_constraints.yaml`) may reference “required metrics”; ensure naming is consistent.

Task dependencies:

- None, temporally. Conceptual alignment only.
