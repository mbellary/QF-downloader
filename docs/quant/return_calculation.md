# Q0.1 — Return Calculation Rules (Canonical)

This document explains the canonical return calculation rules for the system.

Machine-readable authority: `docs/quant/return_calculation.yaml`.

## Goal

Define a single, unambiguous realized return primitive from raw FX bid/ask prices. This return definition is the ground truth for labeling, volatility estimation, regime detection, backtesting, execution validation, and P&L attribution.

## Inputs

- Bid price series (`bid`)
- Ask price series (`ask`)
- Timestamps (ISO-8601)
- Instrument metadata (pair, base/quote currency)

## Canonical price definitions

- Mid price: $mid_t = (bid_t + ask_t) / 2$
- Returns are computed on a declared price series. Default is `mid` for “market move” measurement.
- For executable P&L (fills), use bid/ask asymmetrically as specified in the schema.

## Canonical return primitive

Default primitive is log return:

- $r^{log}_t = \ln(P_t / P_{t-1})$

Simple return is permitted only when explicitly specified:

- $r^{simple}_t = (P_t / P_{t-1}) - 1$

## Time alignment and sessions

- All timestamps are interpreted in UTC.
- A return at time $t$ is computed from the immediately preceding bar close $t-1$ and the current close $t$.
- Session boundaries MUST be explicit. If a daily session concept is needed, the boundary must be defined in UTC and treated deterministically.

## Missing data and gaps

- Gaps and missing previous/current prices MUST produce a null return value plus flags that identify why the return is unavailable.

## Rollover / financing

- This spec defines spot-price returns only.
- If carry/rollover is modeled, it must be a separate additive component with its own sources and alignment rules.

## FX pip and lot conventions

- Pip size is 0.0001 for most FX pairs; 0.01 when the quote currency is JPY.
- Pipette size is pip/10.
- A standard lot is 100,000 units of base currency.

## Acceptance

Engineering can compute returns with zero clarifications by following the machine-readable schema.
