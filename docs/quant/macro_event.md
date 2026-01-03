# Q0.7 — Macro Event Return Attribution Rules

Machine-readable authority: `docs/quant/macro_event.yaml`.

## Goal

Define a reproducible mapping from macro event timestamps to measured market reactions, separating structural event moves from background noise.

## Core concepts

- Explicit pre/post event windows
- An explicit baseline expected return proxy
- Abnormal return: $AR = R_{post} - E[R|baseline]$
- Optional volatility normalization: $AR_{norm} = AR / \sigma_{pre}$

## Overlap

Events must have an explicit overlap policy (default: exclude overlaps).

## Derived artifacts

Downstream teams must generate:

- `targets/macro_event_returns.csv`
- `targets/macro_event_metadata.json`

Derived artifacts must not redefine event windows or abnormal-return logic.
