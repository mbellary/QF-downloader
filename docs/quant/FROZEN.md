# Quant Specification Package — FROZEN

As of 2026-01-02, the Quant Specification Package (Q0) is frozen.

## What is authoritative

Machine-readable schemas under `docs/quant/` (and JSON contracts under `targets/`) are authoritative.

Markdown is explanatory only.

## Immutability rule

No change is permitted without a version bump:

- Update `docs/quant/QUANT_SPEC_VERSION.json`
- Bump `schema_version` in every modified machine-readable artifact

## Downstream hand-off (binding)

Implement directly against the machine-readable schemas.
Markdown is explanatory only.
CI will enforce compliance.
