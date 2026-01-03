# Q0.2 — Backtesting Rules Specification (spec + schema)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This repository defines ExecPlans in PLANS.md (at `PLANS.md` from the repository root). This document must be maintained in accordance with that file.

## Purpose / Big Picture

After this work, historical performance evaluation becomes reproducible and comparable across strategies because the conversion from signals to simulated trades is fully specified with no discretionary interpretation. The observable outcome is that `docs/quant/backtest_rules.md` and `docs/quant/backtest_rules.yaml` exist and describe exactly how to turn a timestamped signal stream into trades, including costs, constraints, and anti-lookahead rules.

## Progress

- [x] (2026-01-02 00:00Z) Created initial ExecPlan for Q0.2.
- [x] (2026-01-02 00:00Z) Created GitHub tracking issue: https://github.com/mbellary/quant-spec/issues/3
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/backtest_rules.md` with complete backtest semantics.
- [x] (2026-01-02 00:00Z) Drafted `docs/quant/backtest_rules.yaml` mirroring the markdown spec.
- [x] (2026-01-02 00:00Z) Ensured the spec explicitly prevents lookahead and survivorship bias.
- [ ] Add at least one worked example: signal → trade → P&L in pips.

- [x] (2026-01-02 00:00Z) Package freeze marker added: `docs/quant/FROZEN.md`.

- [x] (2026-01-02 00:00Z) Artifacts: [docs/quant/backtest_rules.md](../../docs/quant/backtest_rules.md), [docs/quant/backtest_rules.yaml](../../docs/quant/backtest_rules.yaml).

## Surprises & Discoveries

- Observation: Tracking issue numbering may not match Q0 numbering.
  Evidence: Tracking issue created in `Progress` (issue #3 for Q0.2).

- Observation: None yet; implementation has not started.
  Evidence: N/A.

## Decision Log

- Decision: Track this ExecPlan via a dedicated GitHub issue and link it from `Progress`.
  Rationale: Keeps spec work and implementation tracking connected without duplicating status in multiple places.
  Date/Author: 2026-01-02 / Copilot

- Decision: Treat “signal timestamp” and “execution timestamp” as distinct and require an explicit lag rule.
  Rationale: The spec demands elimination of lookahead/execution bias; explicit lag is the simplest enforceable mechanism.
  Date/Author: 2026-01-02 / Copilot

## Outcomes & Retrospective

Not started.

## Context and Orientation

The quant requirements for this task are in `quant_tasks.md` under “Task Q0.2”. Q0 tasks are declarative and co-equal; this specification must not rely on outputs from other Q0 tasks.

The deliverables for this task are a human-readable backtest rulebook and a machine-readable schema, both placed under `docs/quant/`:

- `docs/quant/backtest_rules.md`
- `docs/quant/backtest_rules.yaml`

This spec must be compatible with the return primitive defined in Q0.1, but must not depend on Q0.1 being completed first. Where the backtest refers to returns, it should reference the concept of “canonical realized return” and define how it is obtained from prices (by pointing to the repo artifact path once it exists).

## Task Spec Snapshot (from quant_tasks.md)

### Description

Specifies how trading signals are converted into simulated trades, including entry/exit logic, execution assumptions, transaction costs, and portfolio constraints.

### Objective

Ensure historical performance evaluation is reproducible, comparable, and free from lookahead or execution bias, with no discretionary interpretation.

### Business Use Cases

- Strategy feasibility: avoid paper-only strategies.
- Capital allocation: compare strategies fairly.
- Risk review: backtests must survive audit.
- Bias prevention: eliminate lookahead & survivorship bias.

### Data Providers

Data type required:

- Historical price series
- Spread & cost proxies

Approved providers (examples): Dukascopy, Stooq, Alpha Vantage.

Relevance: costs must reflect deployable cost structures, not paper alpha.

### Inputs

None (pure quant research specification).

### Deliverables

- `backtest_rules.md` describing:
  - entry/exit logic
  - signal lag rules
  - trade frequency limits
  - position sizing formulas
  - volatility gating rules
  - stop-loss & take-profit framework
  - cost model (spread, slippage, financing, rollover)
- `backtest_rules.yaml` encoding the same.

### Outputs

- `docs/quant/backtest_rules.md`
- `docs/quant/backtest_rules.yaml`

### Acceptance Criteria

Backtesting implementation requires zero clarifications.

## Plan of Work

Write a backtesting specification that cleanly separates:

- Market data inputs (bid/ask or bars).
- Signals (what the model emits).
- Execution model (how signals become orders/fills).
- Position/risk constraints (what is allowed).
- Accounting/P&L (how P&L is computed and aggregated).

The spec must explicitly address common sources of bias:

- Lookahead: ensure signals at time $t$ only trade at $t+\Delta$ with defined lag.
- Survivorship: define how instrument universe is selected and fixed for a backtest window.
- Data-snooping: require train/validation/test splits and gating metrics (even if those are defined elsewhere).

The YAML should be an unambiguous representation of the markdown, with enumerated values for things like order types, fill assumptions, and cost components.

## Concrete Steps

From the repository root:

1. Create `docs/quant/backtest_rules.md` and write the spec sections:

   - “Signal Semantics”: allowed signal types (BUY/SELL/FLAT or probabilities), and how to interpret magnitude.
   - “Lag and Alignment”: explicit rule mapping signal timestamps to execution timestamps.
   - “Order and Fill Model”: market vs limit, fill price definition, partial fills assumption.
   - “Costs”: spread, slippage model, commissions (if any), financing/rollover treatment.
   - “Risk and Constraints”: max leverage, max position size, max concurrent positions, cooldown rules.
   - “Stops and TPs”: how SL/TP are set, when evaluated (intrabar vs close-only), and tie-breaking.
   - “Portfolio Accounting”: P&L in pips and in base currency; aggregation rules.

2. Create `docs/quant/backtest_rules.yaml` mirroring the markdown structure.

3. Add a worked example in the markdown:

   - One signal at 10:00, defined lag, entry/exit prices including spread, resulting `pnl_pips`.

4. Validate YAML parses (optional but recommended):

   - `python -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('docs/quant/backtest_rules.yaml').read_text())"`

## Validation and Acceptance

Acceptance is met when:

- Two independent implementers can backtest a simple signal series and produce identical trades and P&L.
- The spec fully defines entry/exit, lag, costs, sizing, and constraints.
- The YAML is parseable and covers all markdown sections with explicit fields.

## Idempotence and Recovery

Edits are safe and repeatable. If YAML parsing fails, fix syntax and re-run the parse command. Keep changes limited to the two artifacts in `docs/quant/`.

## Artifacts and Notes

Expected file creation (after implementation):

- `docs/quant/backtest_rules.md`
- `docs/quant/backtest_rules.yaml`

Illustrative YAML structure (example only):

    execution:
      signal_lag: { unit: "minutes", value: 1 }
      fill_price: "next_bar_open_mid"
    costs:
      spread: { model: "from_data" }
      slippage: { model: "fixed_pips", value: 0.2 }

## Interfaces and Dependencies

This task is declarative and must not depend on other Q0 task outputs.

Interfaces it must align with:

- Return calculation rules (eventual artifact at `docs/quant/return_calculation.yaml`) to avoid double-counting costs vs returns.
- Execution constraints (eventual artifact at `docs/quant/execution_constraints.yaml`) so simulated trading respects real-world limits.

Task dependencies:

- None, temporally. Conceptual alignment only.
