# Q0.2 — Backtesting Rules Specification

Machine-readable authority: `docs/quant/backtest_rules.yaml`.

## Goal

Define how timestamped signals become simulated trades with explicit costs, constraints, and anti-lookahead rules. A backtest that follows this spec should be reproducible and auditable.

## Core rule: signal time vs execution time

Signal timestamps and execution timestamps are distinct.

- A signal at time $t$ may only use information available at $t$.
- The earliest a trade may fill is $t + lag$ (an explicit lag rule).

## Entry/exit

The spec supports deterministic entry/exit modes (e.g., market on next bar close). The chosen mode must be declared.

## Costs

Backtests MUST model costs explicitly:

- Spread costs (in pips)
- Slippage (in pips; explicit model)
- Optional commissions
- Optional financing/rollover as a separate additive component

## Bias prevention

Lookahead is forbidden. The instrument universe must be declared by date to prevent survivorship bias.

## Outputs

Backtests must emit trade-level records including prices, timestamps, P&L (pips and return), and reason codes.
