# Q0.11 — System-Level KPIs & Gating Metrics

Machine-readable authority: `docs/quant/system_kpis.yaml` and `docs/quant/kpi_thresholds.yaml`.

## Goal

Define non-negotiable KPIs that enforce the core objective: separate signal from noise and predict volatility/regimes more reliably than returns.

## Hierarchy (binding)

0) Data integrity & timebase (Phase 0/1 hard gate)
1) Noise separation
2) Volatility prediction
3) Regime identification/stability
4) Conditional alpha
5) Returns (last, not first)

Category 6 (fusion & governance) is an overlay constraint (Phase 3+): it constrains how fusion components (including LLM modifiers) may influence decisions, and must not violate the noise-first priority order.

Return KPIs are necessary but insufficient and must not be evaluated as primary gates.
