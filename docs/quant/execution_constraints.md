# Q0.3 — Execution Constraints Specification

Machine-readable authority: `docs/quant/execution_constraints.yaml`.

## Goal

Define deployable, broker-realistic constraints so both backtests and live systems reject infeasible trades deterministically.

## Constraints are enforceable rules

Constraints MUST be written as allow/deny rules with explicit reasons (not narrative guidance).

## Categories

- Allowed instruments
- Allowed order types
- Size limits (notional, leverage)
- Trading hours (UTC windows)
- Market quality (spread thresholds)
- Risk caps (daily loss limits, exposure limits)

## Required output

Every decision produces:

- `trade_allowed` (boolean)
- `deny_reason` (enumerated reason code)
