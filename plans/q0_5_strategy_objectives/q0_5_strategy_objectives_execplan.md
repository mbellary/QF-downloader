# Q0.5 — Strategy Objective Document (spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, every downstream modeling, optimization, and execution decision can be audited against an explicit trading intent (style, risk profile, turnover expectations, performance targets). The observable outcome is that `docs/quant/strategy_objectives.md` and `docs/quant/strategy_objectives.yaml` exist and provide an unambiguous “north star” that prevents misalignment (e.g., optimizing for a metric that contradicts the intended risk profile).

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.5.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/7
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/strategy_objectives.md`.
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/strategy_objectives.yaml` mirroring the markdown.
- [x] (2026-01-02 00:00Z) Ensured objectives are measurable and include explicit prohibitions.
- [x] (2026-01-02 00:00Z) Validated schema parses (JSON-as-YAML).

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/strategy_objectives.md](../../docs/quant/strategy_objectives.md), [docs/quant/strategy_objectives.yaml](../../docs/quant/strategy_objectives.yaml).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #7 for Q0.5).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Require each objective to specify both target and prohibitions.
  Rationale: Stating only “what we want” is insufficient; explicit non-goals prevent metric gaming.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quant requirements for this task are in `quant_tasks.md` under “Task Q0.5”. Q0 tasks are declarative and co-equal.

This task’s outputs are:

- `docs/quant/strategy_objectives.md`
- `docs/quant/strategy_objectives.yaml`

The quantitative spec also lists `docs/quant/strategy_objectives.yaml` as a global constraint artifact. This task is therefore the source of that “constitutional” document.

## Task Spec Snapshot (from quant_tasks.md)

### Description

Specifies the intended trading style, risk profile, turnover expectations, and target performance characteristics of the overall system.

### Objective

Align all modeling, optimization, and execution decisions with clearly stated economic intent.

### Business Use Cases

The task indicates this document prevents misalignment between model performance and strategy goals and provides a shared definition of intent for quant/ML/engineering.

### Data Providers

This is an intent document; it may reference empirical benchmarks, but does not require a specific market data feed.

### Inputs

None (pure quant research specification).

### Deliverables

- `strategy_objectives.md` describing:
  - intended trading style (e.g., intraday vs swing)
  - target risk profile
  - turnover expectations
  - target performance characteristics
- `strategy_objectives.yaml` encoding the same.

### Outputs

- `docs/quant/strategy_objectives.md`
- `docs/quant/strategy_objectives.yaml`

### Acceptance Criteria

Engineering/ML can make design choices without clarifying “what the strategy is trying to be”.

## Plan of Work

Write an objective spec with explicit, testable statements:

- Instrument scope (FX pairs only vs broader).
- Holding period / trading frequency expectations.
- Risk budget and exposure caps (even if detailed constraints live elsewhere).
- What “success” means in business terms, in a way that can be mapped to KPIs.
- What is explicitly not allowed (e.g., return-chasing at the expense of volatility/regime fidelity).

Mirror the markdown into YAML with stable keys so other docs (KPIs, loss constraints) can reference objectives by key.

## Concrete Steps

From the repository root:

1. Create `docs/quant/strategy_objectives.md` with:

   - “Trading Style”
   - “Risk Profile”
   - “Turnover Expectations”
   - “Performance Characteristics”
   - “Non-Goals and Prohibitions”

2. Create `docs/quant/strategy_objectives.yaml` reflecting the same structure.

3. Validate YAML parses (optional):

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/strategy_objectives.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- The intent is explicit enough that disputes can be resolved by referencing this doc.
- The YAML is parseable and encodes all objective statements as stable keys.

## Idempotence and Recovery

Edits are safe and repeatable. If YAML parsing fails, fix syntax and retry.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/strategy_objectives.md`
- `docs/quant/strategy_objectives.yaml`

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Interfaces it must align with:

- Execution constraints (eventual `docs/quant/execution_constraints.yaml`) so constraints reflect intended risk style.
- System KPIs (eventual `docs/quant/system_kpis.yaml`) so metrics reflect business intent.

Task dependencies:

- None, temporally. Conceptual alignment only.
