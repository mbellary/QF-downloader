# Q0.4 — Validation Metrics

Machine-readable authority: `docs/quant/validation_metrics.yaml`.

## Goal

Define the metric contract used for evaluation and governance. Metrics must be regime-aware and consistent with the system’s noise-first objective.

## Required fields for every metric

Every metric must specify:

- Definition
- Measurement window
- Optimization direction (maximize/minimize)
- Failure modes (how it can mislead)

## Hierarchy

Metrics are interpreted in this priority order:

1) Noise separation
2) Volatility prediction
3) Regime identification
4) Conditional alpha
5) Returns (last)
