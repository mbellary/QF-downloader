# Q0.12 — Quant-Owned ML Training Metrics & Loss Functions (spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, ML model training is constrained to objectives that provably enforce the system’s noise-first principle: noise separation, volatility accuracy, and regime stability are prioritized over returns. The observable outcome is that `docs/quant/loss_constraints.md` and `docs/quant/loss_constraints.yaml` exist and define allowed loss functions, forbidden objectives, required evaluation metrics, and gating conditions.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.12.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/9
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/loss_constraints.md` capturing the full loss/metric/gate policy.
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/loss_constraints.yaml` mirroring the markdown.
- [x] (2026-01-02 00:00Z) Ensured forbidden objectives are explicit and unambiguous.
- [x] (2026-01-02 00:00Z) Validated schema parses (JSON-as-YAML).

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/loss_constraints.md](../../docs/quant/loss_constraints.md), [docs/quant/loss_constraints.yaml](../../docs/quant/loss_constraints.yaml).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #9 for Q0.12).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Encode both “allowed losses” and “hard-stop gates” in the schema.
  Rationale: A list of allowed losses is insufficient without the gating semantics that enforce training order and promotion criteria.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quant requirements for this task are in `quant_tasks.md` under “Task Q0.12”. Q0 tasks are declarative and co-equal.

This task produces:

- `docs/quant/loss_constraints.yaml`
- `docs/quant/loss_constraints.md`

The quantitative spec lists `docs/quant/loss_constraints.yaml` as a global constraint artifact. This task is therefore the source of that “constitutional” training objective contract.

## Task Spec Snapshot (from quant_tasks.md)

### Purpose

Define mandatory loss functions, evaluation metrics, and gating conditions for all ML models such that training provably enforces the system objective: signal must be separated from noise, and volatility/regimes must be predicted more reliably than returns.

### Business Use Cases

- Prevent return-chasing.
- Better risk forecasts (σ accuracy beats returns).
- Stable production behavior.
- Auditability.

### Data Providers

Data type required:

- Targets
- Volatility
- Noise residuals

Approved providers: indirect (derived from real market data; the task text mentions derived from the targets in Q0.6–Q0.9).

### Example Data & Target

- Example: predicted vs realized volatility; example training loss (QLIKE).

### Global Notation

The task defines symbols (e.g., $r_t$, $\epsilon_t$, $\sigma_t$, $z_t$, and loss $\mathcal{L}$) used in the formulas.

### Required loss families, metrics, and prohibitions (high level)

The task text specifies:

- Noise models: NLL, optional jump classification; required KS statistic and moment stability; returns regression is prohibited.
- Volatility models: mandatory QLIKE; secondary log-MSE; required direction accuracy and relative improvement; gate requiring beating a naive baseline.
- Regime models: likelihood-based objectives (HMM/GMM); transition entropy; mutual information with volatility; PnL-based objectives prohibited.
- Directional models: volatility-weighted cross-entropy; conditional hit ratio requirements; maximizing global accuracy prohibited.
- Magnitude models: quantile (pinball) loss; tail calibration.
- Path-dependent outcome models: multinomial cross-entropy; Brier score.
- Fusion/ensemble: composite loss with weight ordering and enforced training gates.
- Global training gates: hard stops based on variance stability, QLIKE improvement, transition entropy, conditional hit ratio, etc.
- Explicitly prohibited objectives: Sharpe, PnL, end-to-end returns.
- Final enforcement statement: improvements in Sharpe with no volatility improvement do not count.

### Non-Negotiable Rule (Business Critical)

Any system iteration that improves returns while degrading noise separation, volatility accuracy, or regime stability is considered a failure regardless of P&L.

### Deliverables

- `loss_constraints.yaml` MUST encode:
  - allowed losses per target type
  - forbidden objectives
  - required metrics
  - fusion loss weight ordering

### Outputs

- `docs/quant/loss_constraints.yaml`
- `docs/quant/loss_constraints.md`

### Acceptance Criteria

No model may be trained/validated/promoted unless it complies with this specification.

## Plan of Work

Write a training objective “policy document” in markdown and a strict schema in YAML.

The policy must contain:

1. Scope and enforcement: which model types are covered, and what it means to be compliant.
2. Allowed losses per target family (noise, volatility, regime, directional, magnitude, path-dependent).
3. Required metrics per family and how to compute them.
4. Prohibited objectives (explicit list, and examples of “nearby” prohibited patterns).
5. Training gates and ordering constraints: what must be proven before training alpha-style models.
6. Fusion/ensemble objective requirements including weight ordering and gating.
7. The business-critical non-negotiable rule (returns improvements that degrade noise/σ/regimes are invalid).

Mirror these rules into YAML with stable identifiers so training pipelines can validate configurations.

## Concrete Steps

From the repository root:

1. Create `docs/quant/loss_constraints.md` with sections matching the required policy above.
2. Create `docs/quant/loss_constraints.yaml` encoding:

   - target families
   - allowed loss functions per family
   - required metrics per family
   - prohibited objectives
   - global gates
   - fusion loss definition and weight ordering

3. Validate YAML parses (optional):

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/loss_constraints.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- The schema makes it impossible (without a conscious schema violation) to configure training that optimizes Sharpe/PnL/returns end-to-end.
- Gating conditions are explicit, measurable, and order-dependent.
- YAML parses successfully.

## Idempotence and Recovery

Edits are safe and repeatable. If YAML parsing fails, fix syntax and retry. Keep changes limited to the two artifacts in `docs/quant/`.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/loss_constraints.md`
- `docs/quant/loss_constraints.yaml`

Illustrative YAML structure (example only):

    families:
      volatility:
        required_losses: ["QLIKE"]
        required_metrics: ["QLIKE", "vol_direction_accuracy"]
      prohibited_objectives: ["sharpe", "pnl", "end_to_end_returns"]

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Interfaces it must align with:

- Feature constraints (eventual `docs/quant/feature_constraints.json`) so allowed objectives and allowed features are consistent.
- System KPI gates (eventual `docs/quant/system_kpis.yaml`) so training gates correspond to system promotion gates.

Task dependencies:

- None, temporally. Conceptual alignment only.
