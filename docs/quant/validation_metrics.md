# Q0.4 — Validation Metrics

Machine-readable authority: `docs/quant/validation_metrics.yaml`.

## Goal

Define the metric contract used for evaluation, governance, and phase gating. Metrics must be regime-aware and consistent with the system’s noise-first doctrine:

- Separate signal from noise.
- Predict volatility and regimes more reliably than returns.
- Treat return improvements without capability improvements as suspect.

## Governance classes (binding)

Every metric MUST be tagged as one of:

- `loss_eligible`: allowed to be optimized directly as an ML loss (when applicable).
- `report_only`: must never be optimized directly as an ML loss.

Additionally, some report-only metrics (notably data/contract diagnostics) MAY be allowed to hard-gate infrastructure phases.

Return / portfolio metrics are always `report_only`.

## Required fields for every metric (binding)

Every metric definition MUST specify:

- Definition (computable)
- Measurement window(s) (e.g., rolling, per-regime)
- Optimization direction (maximize/minimize)
- Failure modes (how it can mislead or be gamed)
- Required conditioning variables (ε/σ/regime gates, masks, regime labels)
- Required visual diagnostics (plots list + acceptance checks)

## Hierarchy (interpretation priority)

Metrics are interpreted in this priority order:

0) Data / contract / governance diagnostics (hard gate for infra readiness)
1) Noise separation
2) Volatility prediction
3) Regime identification/stability
4) Conditional alpha and calibration under gates
5) Returns (last; necessary but insufficient)

## Metric groups (non-exhaustive)

The authoritative YAML enumerates all required metrics across the following groups:

- Data / contract / governance diagnostics (schema compliance, registry completeness, coverage/missingness, timebase integrity, LLM ablation/dominance diagnostics)
- Return / portfolio metrics (reported only; includes cost-adjusted variants)
- Backtest robustness metrics (PBO, DSR, significance checks)
- Signal quality metrics (SNR, IC/Rank-IC, conditional hit rate, alpha decay)
- Probabilistic / calibration metrics (Brier, ECE, log score, reliability)
- Distributional forecast metrics (QLIKE, CRPS/pinball, PIT diagnostics)
- Risk & tail diagnostics (VaR/ES backtests, EVT diagnostics)
- Regime-aware evaluation requirements (per-regime breakdowns, stability across regimes)
