# Q0.10 — Feature Intent & Constraints (Normative)

Machine-readable authority: `docs/quant/feature_constraints.json`.

## Goal

Define feature intent categories and enforceable constraints so that feature engineering serves the noise-first objective and does not introduce leakage, regime confusion, or spurious signal amplification.

## Guiding principle

Features exist to help the system:

1) separate signal from noise,
2) explain/predict volatility and regimes,
3) only then support return prediction.

## Intent taxonomy (exactly one primary intent per feature)

- Signal (α): economically interpretable predictors of conditional return, only usable with noise/volatility/regime gating.
- Noise (ε): measures of randomness, microstructure distortion, jumps; gating/filtering only.
- Volatility (σ): magnitude/risk features; may affect sizing, scaling, and gating; must not encode direction.
- Regime: latent state descriptors; must not be derived from realized P&L.
- Macro & exogenous: external info; must define event alignment and must not leak post-event outcomes.

## Temporal constraints (mandatory declarations)

Each feature must declare:

- Lookback horizon
- Update frequency
- Alignment (bar/session/event)
- Latency tolerance

## Usage constraints

Each feature must declare allowed usage areas. Reuse outside declared usage is forbidden.

## Leakage prohibitions

Explicitly prohibited:

- Future returns or prices
- Realized P&L encoding
- Post-trade information
- Any construction that depends on target outcomes

## Documentation requirements

Every downstream feature must carry metadata required by the machine-readable constraint schema.
