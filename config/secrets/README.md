# Local secrets (not committed)

Create a local secrets file at `config/secrets/fx_api_keys.json`.

- Start from `config/secrets/fx_api_keys.example.json`
- Replace `REPLACE_ME` with your real API keys
- This repo ignores `config/secrets/*.json` to prevent accidental commits

Runtime resolution (Phase 0.1):
- Prefer environment variables for CI/production
- Use `config/secrets/fx_api_keys.json` for local development
