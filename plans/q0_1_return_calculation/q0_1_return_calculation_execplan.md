# Q0.1 — Return Calculation Rules (spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, anyone (engineering, ML, quant, finance) can compute realized FX returns from raw bid/ask prices with zero ambiguity. The observable outcome is that the repo contains a canonical return specification at `docs/quant/return_calculation.md` and a machine-readable schema at `docs/quant/return_calculation.yaml`, and two independent implementers produce matching returns on the same sample input.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.1.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/2
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/return_calculation.md` with the full rule set.
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/return_calculation.yaml` mirroring the markdown spec.
- [x] (2026-01-02 00:00Z) Validated that the machine-readable schema parses (JSON-as-YAML) and is consistent with the markdown.
- [ ] Add a small worked example in the markdown and confirm two independent calculations agree.

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/return_calculation.md](../../docs/quant/return_calculation.md), [docs/quant/return_calculation.yaml](../../docs/quant/return_calculation.yaml).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #2 for Q0.1).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Use log returns as the default return primitive, but explicitly specify when simple returns are permitted.
  Rationale: The quantitative spec requires a single unambiguous primitive; log returns are additive across time and common for volatility/regime work.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quantitative specification is authored in `quant_tasks.md` and defines a set of Q0 tasks (declarative, co-equal) that must not depend on each other temporally. This task (Q0.1) defines the canonical realized return computation from raw FX data.

The output artifacts for this task must live under `docs/quant/`:

- `docs/quant/return_calculation.md`
- `docs/quant/return_calculation.yaml`

Global system constraints are described as “constitutional” artifacts under `docs/quant/` (for example `docs/quant/system_kpis.yaml`, `docs/quant/loss_constraints.yaml`, `docs/quant/feature_constraints.json`, `docs/quant/strategy_objectives.yaml`). Per the Q0 rules in `quant_tasks.md`, these must not be listed as inputs to this task, but the return definition must be consistent with them once they exist.

Terminology used in this plan:

- “Mid price”: $(bid + ask) / 2$.
- “Log return”: $\log(P_t / P_{t-1})$.
- “Simple return”: $(P_t / P_{t-1}) - 1$.
- “Session boundary”: a deterministic rule for defining open/close timestamps and how to handle gaps, weekends, or market holidays.
- “Rollover”: end-of-day financing / swap effects that can impact P&L but are not always embedded in spot price series.

## Task Spec Snapshot (from quant_tasks.md)

### Description

Defines the canonical method for computing realized returns from raw FX price data, including price selection, session boundaries, rollover handling, and contract conventions.

### Objective

Establish a single, unambiguous return primitive that serves as the ground truth for labeling, volatility estimation, regime detection, backtesting, execution validation, and P&L attribution.

### Business Use Cases

- P&L attribution: finance must reconcile strategy vs broker.
- Model labeling: ML needs consistent ground truth.
- Volatility estimation: volatility models depend on correct returns.
- Cross-team consistency: prevent multiple return definitions.

### Data Providers

Data type required:

- FX bid/ask prices
- Session timestamps
- Contract conventions

Approved providers (examples): Dukascopy, TrueFX, Alpha Vantage, Stooq.

Relevance: return definitions must align with real bid/ask spreads (not mid-only “fantasy” pricing).

### Inputs

None (pure quant research specification).

### Deliverables

- `return_calculation.md` describing:
  - log returns vs simple returns
  - bid/ask selection
  - session boundaries
  - FX pip/pipette/pip-value conventions
  - leverage/contract specifications
  - timezone handling
- `return_calculation.yaml` encoding the same concepts.

### Outputs

- `docs/quant/return_calculation.md`
- `docs/quant/return_calculation.yaml`

### Acceptance Criteria

Engineering can compute returns with no ambiguity.

## Plan of Work

Write a “single source of truth” return definition that covers:

1. Price definition: exactly which price series is used for returns (bid, ask, mid) and under what circumstances.
2. Time alignment: how timestamps are bucketed (tick to bar), and how the return at time $t$ is aligned to input prices.
3. Session boundaries and calendar: explicit timezone, handling of weekends, DST, market holidays, and gaps.
4. Rollover and financing: explicitly state whether returns are price-only, carry-inclusive, or whether carry is a separate P&L component.
5. Contract and pip conventions: define pip size, pip value, lot size, leverage assumptions, and how to convert price moves to pips and P&L.

The markdown and YAML must be isomorphic: each concept in markdown has a corresponding YAML field so downstream code can be generated/validated.

## Concrete Steps

From the repository root:

1. Create `docs/quant/return_calculation.md` and write the specification:

   - Start with definitions of mid/bid/ask, log vs simple returns.
   - Add a section “Canonical Return Primitive” that states the default formula.
   - Add a section “Timestamp and Session Rules” that defines timezone and boundaries.
   - Add a “Rollover and Carry” section that explicitly states inclusion/exclusion.
   - Add a “Pip and Contract Conventions” section with explicit numeric conventions (pip size per major pair) and conversion formulas.
   - Add a short worked example (two timestamps, bid/ask, resulting return).

2. Create `docs/quant/return_calculation.yaml` that mirrors the markdown structure.

3. Validate YAML parses (optional but recommended):

   - If Python 3 is available:

     - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/return_calculation.yaml').read_text())"`

   - Expected outcome: command exits with status 0 and prints nothing.

4. Consistency check: read both files and ensure every markdown decision is representable in YAML.

## Validation and Acceptance

Acceptance is met when:

- A reader can implement return computation without asking questions about:
  - which price (bid/ask/mid) is used
  - which timestamps define a return interval
  - what timezone the “day” boundary uses
  - what happens at session gaps/weekends
  - whether rollover/carry is included
  - how pips and contract sizing are handled
- The YAML file parses successfully and contains fields covering all major sections of the markdown.
- The markdown includes at least one worked example whose computed return is numerically consistent.

## Idempotence and Recovery

Creating or editing these two files is safe and repeatable. If YAML validation fails, fix syntax errors and re-run the validation command until it parses. Keep changes limited to `docs/quant/return_calculation.md` and `docs/quant/return_calculation.yaml`.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/return_calculation.md`
- `docs/quant/return_calculation.yaml`

Example snippet (illustrative structure only):

    canonical_return:
      type: log_return
      price: mid
      formula: "log(P_t / P_{t-1})"
    timezone: "UTC"

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Dependencies and interfaces to anticipate:

- Downstream backtesting and execution will consume this return primitive; therefore the spec must explicitly separate “price return” from “trade P&L” components (spread, slippage, financing) to avoid double-counting.
- The schema should be stable and machine-readable: prefer explicit keys over prose-only descriptions.
- The output paths are fixed:
  - `docs/quant/return_calculation.md`
  - `docs/quant/return_calculation.yaml`
