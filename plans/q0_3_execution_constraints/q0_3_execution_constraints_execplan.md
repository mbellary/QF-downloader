# Q0.3 — Execution Constraints Specification (spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, the system has an explicit, broker-realistic envelope for what trades are allowed, when they are allowed, and how large they may be. The observable outcome is that `docs/quant/execution_constraints.md` and `docs/quant/execution_constraints.yaml` exist and can be used by both backtests and live execution to reject infeasible trades with deterministic reasons.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.3.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/4
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/execution_constraints.md` (human-readable rulebook).
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/execution_constraints.yaml` (machine-readable schema).
- [x] (2026-01-02 00:00Z) Ensured constraints are written as enforceable rules (not vague guidance).
- [ ] Include at least one example: instrument/spread/size → trade_allowed + reason.

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/execution_constraints.md](../../docs/quant/execution_constraints.md), [docs/quant/execution_constraints.yaml](../../docs/quant/execution_constraints.yaml).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #4 for Q0.3).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Encode constraints as explicit “allow/deny with reason” predicates in YAML.
  Rationale: This makes it easy for engineering to implement consistent gating logic in both backtests and production.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quant requirements for this task are in `quant_tasks.md` under “Task Q0.3”. Q0 tasks are declarative and co-equal and must not depend on each other.

This task’s artifacts live under `docs/quant/`:

- `docs/quant/execution_constraints.md`
- `docs/quant/execution_constraints.yaml`

These constraints are intended to be used by:

- Backtesting (to avoid simulating impossible trades).
- Live execution (to prevent rejected orders and operational incidents).

## Task Spec Snapshot (from quant_tasks.md)

### Description

Defines real-world trading constraints such as allowed instruments, order types, size limits, trading hours, spread thresholds, and risk caps.

### Objective

Guarantee that all strategies, backtests, and live execution operate within deployable and broker-realistic boundaries.

### Business Use Cases

- Broker compatibility: prevent rejected orders.
- Liquidity protection: avoid trading thin markets.
- Risk limits: enforce VaR & exposure caps.
- Operational safety: prevent off-hours trading.

### Data Providers

Data type required:

- Typical spreads
- Trading hours
- Liquidity proxies

Approved providers (examples): Dukascopy, TrueFX, broker public specs (OANDA, IBKR).

Relevance: constraints must reflect what brokers actually allow.

### Inputs

None (pure quant research specification).

### Deliverables

- `execution_constraints.md` describing:
  - allowed instruments
  - min/max size
  - order types (market, limit)
  - allowed trading hours
  - permissible spread thresholds
  - risk limits (VaR, volatility exposure)
- `execution_constraints.yaml` encoding the same.

### Outputs

- `docs/quant/execution_constraints.md`
- `docs/quant/execution_constraints.yaml`

## Plan of Work

Write enforceable constraints in two layers:

1. Static constraints: instrument allowlist/denylist, order types, min/max order sizes.
2. Dynamic constraints: spread threshold checks, trading hours, volatility gates, and portfolio risk caps.

Each constraint should specify:

- What it checks (inputs needed).
- The exact condition (mathematical or logical).
- The failure reason string/identifier that must be returned.

The YAML should allow engineering to implement a deterministic function like:

- `is_trade_allowed(context) -> { allowed: bool, reasons: [..] }`

## Concrete Steps

From the repository root:

1. Create `docs/quant/execution_constraints.md` and write:

   - “Instruments”: list allowed pairs and any exclusions.
   - “Order Types”: define allowed order types and any parameters.
   - “Sizing”: min/max lots and step size.
   - “Trading Hours”: timezone, session windows, holiday/weekend rules.
   - “Spread and Liquidity”: define spread thresholds and how spread is measured.
   - “Risk Caps”: define max exposure, VaR limits, volatility exposure caps.

2. Create `docs/quant/execution_constraints.yaml` mirroring those sections with explicit keys and enumerations.

3. Add a worked example in the markdown:

   - Example: EURUSD, spread=0.9 pips, order_size=5 lots → allowed=true.
   - Example: spread above threshold → allowed=false with reason.

4. Validate YAML parses (optional):

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/execution_constraints.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- An implementer can build a constraints checker without asking for missing definitions.
- Constraints are written in a way that can be applied uniformly to backtests and live execution.
- YAML parses and contains all constraints as explicit, machine-readable rules.

## Idempotence and Recovery

Editing these spec files is safe and repeatable. YAML parse validation can be re-run after each edit.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/execution_constraints.md`
- `docs/quant/execution_constraints.yaml`

Illustrative YAML structure (example only):

    instruments:
      allowed: ["EURUSD", "GBPUSD"]
    spread:
      max_pips: 1.5
      measurement: "bid_ask" 

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Interfaces it must align with:

- Backtesting rules (eventual artifact `docs/quant/backtest_rules.yaml`) for consistent enforcement.
- Strategy objectives (eventual artifact `docs/quant/strategy_objectives.yaml`) to match allowable instruments and risk profile.

Task dependencies:

- None, temporally. Conceptual alignment only.
