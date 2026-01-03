# Q0.8 — Microstructure Target Definitions

Machine-readable authority: `docs/quant/microstructure.yaml`.

## Goal

Define tick-aligned, causally valid microstructure targets (≤ 5 minutes horizons) such as order-flow imbalance and liquidity shocks.

## Causality

Targets must be computed using only past and current ticks relative to the target timestamp.

## Horizon isolation

Microstructure horizons must not exceed 5 minutes and must not overlap directional horizons.

## Derived artifacts

Downstream teams must generate:

- `targets/microstructure_targets.parquet`
- `targets/microstructure_schema.json`

Derived artifacts must not redefine OFI logic or extend horizons.
