# KPI Thresholds

Machine-readable authority: `docs/quant/kpi_thresholds.yaml`.

This document explains phase gating thresholds and degradation tolerances. Thresholds may be absolute or relative-to-baseline, but must be machine-readable.

## Phases

The threshold schema defines required KPI gates for phases `PHASE_0` through `PHASE_5`.

- Phase 0: data integrity & timebase hard gates (Category 0)
- Phase 1–2: capability gates (noise/volatility/regime/conditional alpha)
- Phase 3+: governance and fusion constraints (Category 6) become mandatory gates
- Returns remain last and are prohibited as primary promotion gates

## Threshold types (contract)

Each threshold entry includes a `type` field. Current types used:

- `min_absolute`: value must be >= `min`
- `max_absolute`: value must be <= `max`
- `relative_to_baseline`: value must be >= baseline + `delta_min` (baseline defined by implementation policy)
- `beat_baseline`: value must be strictly better than a named baseline (e.g., `naive_rolling_rv`)
- `gt_other`: value must be > another KPI computed on the same evaluation set
- `max_degradation`: value must not degrade by more than `tolerance` relative to the last certified phase

## Governance intent

Thresholds are defined as a constitutional minimum. Downstream deployments MAY tighten thresholds, but must not loosen them without a version bump to the authoritative machine-readable artifacts.

## Phase gating summary (executive view)

| Phase   | Hard gate KPI categories |
| ------- | ------------------------ |
| Phase 0 | Data/timebase integrity + contract compliance |
| Phase 1 | Noise explainability, volatility accuracy, regime stability |
| Phase 2 | Conditional alpha, regime consistency, calibration |
| Phase 3 | Noise gating effectiveness, volatility dominance, fusion governance |
| Phase 4 | Live degradation tolerances |
| Phase 5 | Drift in noise/σ/regimes (not returns) |
