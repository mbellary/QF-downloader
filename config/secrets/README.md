# Local secrets (not committed)

Create a local secrets file at `config/secrets/fx_api_keys.json`.

- Start from `config/secrets/fx_api_keys.example.json`
- Replace `REPLACE_ME` with your real API keys
- This repo ignores `config/secrets/*.json` to prevent accidental commits

Runtime resolution (Phase 0.1):
- Prefer environment variables for CI/production
- Use `config/secrets/fx_api_keys.json` for local development

## Google Drive (FX-1-Minute-data)

To ingest from a Google Drive folder, create one of the following (not committed):

- `config/secrets/google_drive_service_account.json` (recommended for non-interactive runs)
- `config/secrets/google_drive_authorized_user.json` (OAuth *authorized user* JSON that includes a refresh token)

Then configure a provider entry in `config/vendors/fx_providers.json` with:

- `source: "google_drive"`
- `google_drive.root_folder_id` (the folder id for your `FX-1-Minute-data` folder)
- `auth.type: "google_drive_service_account"` (or `google_drive_authorized_user`)

Notes:
- If you use a service account, you must share the Google Drive folder with the service account email.
- You can also override credential paths via env vars:
	- `GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE`
	- `GOOGLE_DRIVE_AUTHORIZED_USER_FILE`
