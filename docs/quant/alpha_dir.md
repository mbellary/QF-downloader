# Q0.6 — Directional Label Construction Rules

Machine-readable authority: `docs/quant/alpha_dir.yaml`.

## Goal

Define directional labels $Y_{dir} \in \{-1,0,+1\}$ that are economically meaningful, statistically stable, and explicitly downstream of noise and volatility.

## Label definition

For horizon $h$:

- $+1$ if $r_{t\rightarrow t+h} > \theta(\sigma_t)$
- $-1$ if $r_{t\rightarrow t+h} < -\theta(\sigma_t)$
- $0$ otherwise

Default threshold is volatility-scaled: $\theta(\sigma_t)=k\cdot\sigma_t$, with $k>0$.

## Non-negotiable constraint

Zero-threshold labels (effectively always non-zero) are disallowed unless explicitly approved and encoded in the machine-readable schema.

## Regime conditioning

If regime labels are present, thresholds may vary by regime and class balance must be reported per regime.

## Derived artifacts

Downstream teams must generate:

- `targets/alpha_dir_labels.csv`
- `targets/alpha_dir_label_metadata.json`

These derived artifacts must not redefine the label logic.
