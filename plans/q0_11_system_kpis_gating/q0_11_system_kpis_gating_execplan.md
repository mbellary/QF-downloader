# Q0.11 — System-Level KPIs & Gating Metrics (spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, the system has a “noise-first” KPI framework and explicit phase gates that prevent promotion of models/strategies that improve returns while degrading noise separation, volatility accuracy, or regime stability. The observable outcome is that the repo contains KPI semantics and thresholds at `docs/quant/system_kpis.md`, `docs/quant/system_kpis.yaml`, `docs/quant/kpi_thresholds.md`, and `docs/quant/kpi_thresholds.yaml`, and that these documents define measurable metrics, thresholds, and degradation tolerances.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.11.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/12
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/system_kpis.md` and `docs/quant/system_kpis.yaml`.
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/kpi_thresholds.md` and `docs/quant/kpi_thresholds.yaml`.
- [x] (2026-01-02 00:00Z) Ensured KPI priority ordering is noise → volatility → regime → alpha → returns.
- [x] (2026-01-02 00:00Z) Validated schemas parse (JSON-as-YAML).

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/system_kpis.md](../../docs/quant/system_kpis.md), [docs/quant/system_kpis.yaml](../../docs/quant/system_kpis.yaml), [docs/quant/kpi_thresholds.md](../../docs/quant/kpi_thresholds.md), [docs/quant/kpi_thresholds.yaml](../../docs/quant/kpi_thresholds.yaml).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #12 for Q0.11).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Split KPI semantics from KPI thresholds into separate artifacts.
  Rationale: Semantics should be stable across environments; thresholds and tolerances may vary by phase or deployment context.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quant requirements for this task are in `quant_tasks.md` under “Task Q0.11”. Q0 tasks are declarative and co-equal.

This task produces four artifacts under `docs/quant/`:

- `docs/quant/system_kpis.md`
- `docs/quant/system_kpis.yaml`
- `docs/quant/kpi_thresholds.md`
- `docs/quant/kpi_thresholds.yaml`

The quantitative spec lists `docs/quant/system_kpis.yaml` as a global constraint artifact. This task is therefore the source of that “constitutional” KPI contract.

## Task Spec Snapshot (from quant_tasks.md)

### Purpose

Define non-negotiable key metrics that enforce the core objective: separate signal from noise and predict volatility/regimes more reliably than returns. KPIs act as phase gates; no phase may progress unless required KPIs are met.

### Business Use Cases

- Capital protection (stop weak models early).
- Lifecycle governance (control phase progression).
- Risk committee review.
- False-confidence prevention.

### Data Providers

Data types required: returns, volatility, regime indicators, event context. Approved providers: composite of all above.

### Example Data & Target

Example: KPI QLIKE value 0.42 implies `phase_gate_pass = TRUE` (illustrative).

### Guiding Principle

Returns are an outcome; noise separation, volatility accuracy, and regime stability are capabilities. Return improvements without capability improvement are invalid.

### Metric Hierarchy (Very Important)

Explicit priority ordering:

1) Noise separation KPIs (ε)
2) Volatility prediction KPIs (σ)
3) Regime identification KPIs
4) Conditional alpha KPIs
5) Return-based KPIs (last)

### KPI Categories and Examples

The task defines multiple KPIs with formulas and gates, including (non-exhaustive):

- Noise Explainability Ratio (NER): $NER = (Var(\hat{\epsilon}) + Var(\hat{\sigma})) / Var(r)$, with phase-dependent gates.
- Noise Gating Effectiveness (NG): reduction in trades during high-noise regimes.
- Jump Containment Ratio (JCR): fraction of detected jumps filtered out.
- Volatility forecast accuracy: QLIKE, MSE, directional accuracy; must beat naive baseline.
- Volatility Dominance Ratio (VDR): fraction of decisions gated by σ.
- Regime predictability and regime-conditional consistency.
- Conditional hit ratio and alpha decay half-life.
- Return metrics (Sharpe/Sortino/drawdown) gated only after 1–4 pass.

### Phase Gating Summary

The task includes an executive summary table of which KPI categories gate which phases (Phase 0–5).

### Inputs

None (pure quant research specification).

### Deliverables

From the quant spec:

- `kpi_thresholds.yaml` MUST encode:
  - KPI names
  - thresholds
  - phase applicability
  - degradation tolerances
- `system_kpis.yaml` MUST encode:
  - canonical KPI names and identifiers
  - KPI category and priority ordering (noise → volatility → regime → alpha → returns)
  - formal metric definitions and measurement formulas
  - economic interpretation and optimization direction
  - valid value ranges and degradation semantics
  - governance rules and prohibitions
  - cross-phase reference contract for CI/runtime gating/certification
- `kpi_thresholds.md` and `system_kpis.md` describing the detailed task.

### Outputs

- `docs/quant/kpi_thresholds.md`
- `docs/quant/kpi_thresholds.yaml`
- `docs/quant/system_kpis.md`
- `docs/quant/system_kpis.yaml`

### Acceptance Criteria

KPIs are measurable, prioritized correctly, and usable as hard promotion gates.

## Plan of Work

Write KPI semantics first, then thresholds:

1. KPI semantics:

   - Define KPI identifiers and categories.
   - For each KPI: definition, formula, required inputs, interpretation, valid ranges.
   - Encode governance prohibitions (e.g., “no return-first KPIs”).

2. Thresholds:

   - Define phase-specific thresholds and degradation tolerances.
   - Ensure explicit phase applicability for each KPI.

Mirror both documents into YAML schemas with stable IDs, so CI and runtime gating can reference KPIs by key.

## Concrete Steps

From the repository root:

1. Create `docs/quant/system_kpis.md` and `docs/quant/system_kpis.yaml`.
2. Create `docs/quant/kpi_thresholds.md` and `docs/quant/kpi_thresholds.yaml`.
3. Validate YAML parses (optional):

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/system_kpis.yaml').read_text())"`
   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/kpi_thresholds.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- KPI priority ordering is explicit and matches the system-level principle.
- Every KPI has a formula, direction (higher/lower better), and valid range.
- Thresholds are phase-specific and include degradation tolerances.
- Both YAML files parse successfully.

## Idempotence and Recovery

Edits are safe and repeatable. If YAML parsing fails, fix syntax and retry.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/system_kpis.md`
- `docs/quant/system_kpis.yaml`
- `docs/quant/kpi_thresholds.md`
- `docs/quant/kpi_thresholds.yaml`

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Interfaces it must align with:

- Validation metrics catalog (eventual `docs/quant/validation_metrics.yaml`) for metric IDs and formulas.
- Loss constraints (eventual `docs/quant/loss_constraints.yaml`) for required training metrics and gates.

Task dependencies:

- None, temporally. Conceptual alignment only.
