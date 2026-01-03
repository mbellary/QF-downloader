# Q0.9 — Path-Dependent Outcome Labeling (SL/TP)

Machine-readable authority: `docs/quant/path_outcomes.yaml`.

## Goal

Define SL/TP outcome labels from full price paths (including intrabar extremes) using volatility-scaled barriers.

## Barriers

- $SL = -k_{sl} \cdot \sigma_t$
- $TP = +k_{tp} \cdot \sigma_t$

## Path dependence

Close-to-close labeling is invalid for SL/TP. Intrabar extremes must be used.

## Tie-breaking

If SL and TP are both reachable within a bar and tick ordering is unknown, the default policy must be conservative (SL first) unless the data source provides orderable ticks.

## Derived artifacts

Downstream teams must generate:

- `targets/path_outcomes.parquet`
- `targets/path_label_metadata.json`
