# Q0.12 — Loss Constraints (Training Objectives)

Machine-readable authority: `docs/quant/loss_constraints.yaml`.

## Goal

Constrain ML training objectives so that noise separation, volatility accuracy, and regime stability are prioritized over returns.

## Non-negotiable rule

Any iteration that improves returns while degrading noise separation, volatility accuracy, or regime stability is a failure regardless of P&L.

## Key requirements

- Volatility models must use QLIKE (mandatory) and must beat a naive baseline before any directional training is considered.
- Return-optimizing objectives (PnL, Sharpe, end-to-end returns) are explicitly prohibited.
- Fusion losses must enforce a weight ordering that prioritizes ε and σ over α.
