from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


@dataclass(frozen=True)
class GoogleDriveAuthConfig:
    """Resolved auth config for Google Drive."""

    auth_type: str
    service_account_file: Path | None = None
    authorized_user_file: Path | None = None
    scopes: tuple[str, ...] = (DRIVE_READONLY_SCOPE,)


class GoogleDriveClient:
    """Small wrapper around Google Drive v3.

    Designed to keep Google API usage localized and easy to mock in tests.
    """

    def __init__(self, service: Any):
        self._service = service
        self._folder_cache: dict[tuple[str, str], str] = {}

    @classmethod
    def from_provider(cls, *, provider: dict[str, Any], repo_root: Path) -> "GoogleDriveClient":
        auth_cfg = provider.get("auth") or {}
        if not isinstance(auth_cfg, dict):
            auth_cfg = {}

        resolved = _resolve_auth_config(auth_cfg=auth_cfg, repo_root=repo_root)
        creds = _load_credentials(resolved)

        # Import lazily so non-gdrive users don't pay import cost at CLI startup.
        from googleapiclient.discovery import build  # type: ignore

        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return cls(service=service)

    def find_child_folder_id(self, *, parent_folder_id: str, folder_name: str) -> str | None:
        cache_key = (parent_folder_id, folder_name)
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        q = (
            f"'{parent_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"name='{_escape_drive_q_string(folder_name)}' and trashed=false"
        )

        resp = (
            self._service.files()
            .list(
                q=q,
                fields="files(id,name)",
                pageSize=10,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        files = resp.get("files", []) if isinstance(resp, dict) else []
        if not files:
            return None

        folder_id = str(files[0].get("id"))
        if folder_id:
            self._folder_cache[cache_key] = folder_id
        return folder_id

    def find_folder_id_by_name(self, *, folder_name: str) -> str | None:
        """Find a folder by name anywhere visible to the principal.

        This is best-effort: if multiple folders share a name, the first match is returned.
        Prefer using folder ids for determinism.
        """

        q = (
            "mimeType='application/vnd.google-apps.folder' and "
            f"name='{_escape_drive_q_string(folder_name)}' and trashed=false"
        )
        resp = (
            self._service.files()
            .list(
                q=q,
                fields="files(id,name)",
                pageSize=10,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        files = resp.get("files", []) if isinstance(resp, dict) else []
        if not files:
            return None
        return str(files[0].get("id"))

    def find_file_id_by_name(self, *, folder_id: str, filename: str) -> str | None:
        q = (
            f"'{folder_id}' in parents and "
            f"name='{_escape_drive_q_string(filename)}' and trashed=false"
        )

        resp = (
            self._service.files()
            .list(
                q=q,
                fields="files(id,name,size,md5Checksum)",
                pageSize=10,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        files = resp.get("files", []) if isinstance(resp, dict) else []
        if not files:
            return None
        return str(files[0].get("id"))

    def download_file_bytes(self, *, file_id: str) -> bytes:
        from io import BytesIO

        # MediaIoBaseDownload handles chunking and retries at the HTTP layer.
        from googleapiclient.http import MediaIoBaseDownload  # type: ignore

        request = self._service.files().get_media(fileId=file_id, supportsAllDrives=True)

        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024)
        done = False
        while not done:
            _status, done = downloader.next_chunk()

        return fh.getvalue()


def _resolve_auth_config(*, auth_cfg: dict[str, Any], repo_root: Path) -> GoogleDriveAuthConfig:
    auth_type = str(auth_cfg.get("type") or "").strip()

    scopes_raw = auth_cfg.get("scopes")
    scopes: tuple[str, ...]
    if isinstance(scopes_raw, list) and scopes_raw:
        scopes = tuple(str(s) for s in scopes_raw)
    elif isinstance(scopes_raw, str) and scopes_raw.strip():
        scopes = (scopes_raw.strip(),)
    else:
        scopes = (DRIVE_READONLY_SCOPE,)

    # Prefer explicit provider config; fall back to environment; then default path.
    # if auth_type == "google_drive_service_account":
    #     p = auth_cfg.get("service_account_file")
    #     if not p:
    #         import os

    #         p = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
    #     if not p:
    #         p = str(repo_root / "config" / "secrets" / "google_drive_service_account.json")
    #     return GoogleDriveAuthConfig(
    #         auth_type=auth_type,
    #         service_account_file=Path(p),
    #         scopes=scopes,
    #     )

    if auth_type == "google_drive_service_account":
        import os

        # 1️⃣ Highest priority: env var
        env_path = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
        if env_path:
            return GoogleDriveAuthConfig(
                auth_type=auth_type,
                service_account_file=Path(env_path),
                scopes=scopes,
            )

        # 2️⃣ Optional explicit config (ONLY if non-empty)
        cfg_path = auth_cfg.get("service_account_file")
        if isinstance(cfg_path, str) and cfg_path.strip():
            return GoogleDriveAuthConfig(
                auth_type=auth_type,
                service_account_file=Path(cfg_path),
                scopes=scopes,
            )

        # 3️⃣ Legacy fallback (local dev only)
        legacy = repo_root / "config" / "secrets" / "google_drive_service_account.json"
        return GoogleDriveAuthConfig(
            auth_type=auth_type,
            service_account_file=legacy,
            scopes=scopes,
        )

    if auth_type == "google_drive_authorized_user":
        p = auth_cfg.get("authorized_user_file")
        if not p:
            import os

            p = os.getenv("GOOGLE_DRIVE_AUTHORIZED_USER_FILE")
        if not p:
            p = str(repo_root / "config" / "secrets" / "google_drive_authorized_user.json")
        return GoogleDriveAuthConfig(
            auth_type=auth_type,
            authorized_user_file=Path(p),
            scopes=scopes,
        )

    raise ValueError(
        "Google Drive provider requires auth.type to be one of: "
        "google_drive_service_account | google_drive_authorized_user"
    )


def _load_credentials(cfg: GoogleDriveAuthConfig):
    if cfg.auth_type == "google_drive_service_account":
        if cfg.service_account_file is None:
            raise ValueError("Missing service_account_file")
        if not cfg.service_account_file.exists():
            raise FileNotFoundError(f"Service account JSON not found: {cfg.service_account_file}")

        from google.oauth2 import service_account  # type: ignore

        return service_account.Credentials.from_service_account_file(
            str(cfg.service_account_file), scopes=list(cfg.scopes)
        )

    if cfg.auth_type == "google_drive_authorized_user":
        if cfg.authorized_user_file is None:
            raise ValueError("Missing authorized_user_file")
        if not cfg.authorized_user_file.exists():
            raise FileNotFoundError(f"Authorized user JSON not found: {cfg.authorized_user_file}")

        from google.oauth2.credentials import Credentials  # type: ignore

        creds = Credentials.from_authorized_user_file(
            str(cfg.authorized_user_file),
            scopes=cfg.scopes,
        )
        if not creds.valid:
            # Refresh if possible.
            if creds.refresh_token:
                from google.auth.transport.requests import Request  # type: ignore

                creds.refresh(Request())
        return creds

    raise ValueError(f"Unsupported auth_type: {cfg.auth_type}")


def _escape_drive_q_string(value: str) -> str:
    # Drive query uses single quotes for string literals; escape by backslash.
    return value.replace("\\", "\\\\").replace("'", "\\'")
