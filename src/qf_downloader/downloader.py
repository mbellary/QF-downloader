import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Tuple

import aiohttp
from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from qf_downloader.config import S3_BUCKET
from qf_downloader.db import DownloadDB
from qf_downloader.logger import get_logger
from qf_downloader.storage import S3Client
from qf_downloader.utils import ensure_dir, guess_content_type

from .metadata import build_sidecar_metadata, update_rollup_manifest
from .s3_indexer import S3Indexer

logger = get_logger("downloader.downloader")


class ProviderDownloader:
    def __init__(
        self, provider: Dict[str, Any], s3: S3Client, db: DownloadDB, base_data_dir="./data"
    ):
        self.provider = provider
        self.s3 = s3
        self.db = db
        self.base_data_dir = base_data_dir
        self.indexer = S3Indexer()

    # ---------------------------------------------------------
    # MULTI-PAIR: DOWNLOAD *ALL* SUPPORTED PAIRS FOR TODAY
    # ---------------------------------------------------------
    async def download_and_upload(self):
        pairs = self.provider.get("supports_pairs", [])
        results = []
        for pair in pairs:
            r = await self._download_single_day(pair, datetime.now(UTC))
            results.append(r)
        return results

    # ---------------------------------------------------------
    # BACKFILL: DATE RANGE
    # ---------------------------------------------------------
    async def backfill_range(self, start, end):
        if (
            self._is_google_drive_provider(self.provider)
            and self._google_drive_granularity() == "year"
        ):
            for year in range(int(start.year), int(end.year) + 1):
                day = datetime(year, 1, 1, tzinfo=UTC)
                for pair in self.provider.get("supports_pairs", []):
                    await self._download_single_day(pair, day)
            return

        day = start
        while day <= end:
            for pair in self.provider.get("supports_pairs", []):
                await self._download_single_day(pair, day)
            day += timedelta(days=1)

    # ---------------------------------------------------------
    # SINGLE DAY DOWNLOAD FOR A SINGLE PAIR
    # ---------------------------------------------------------
    async def _download_single_day(self, pair: str, day: datetime):
        yyyy = day.strftime("%Y")
        mm = day.strftime("%m")
        dd = day.strftime("%d")
        date = f"{yyyy}{mm}{dd}"
        start_date = day.strftime("%Y-%m-%d")
        end_date = start_date

        artifact_type = self.provider.get("artifact_type") or self.provider.get("type")
        if artifact_type:
            artifact_type = str(artifact_type).lower()

        base, quote = self._split_pair(pair)

        is_google_drive = self._is_google_drive_provider(self.provider)

        url_template = self.provider.get("url_template")
        if not url_template and not is_google_drive:
            logger.error(f"Provider {self.provider['name']} has no url_template")
            return

        template_vars: dict[str, str] = {
            "pair": pair,
            "pair_lower": pair.lower(),
            "base": base,
            "quote": quote,
            "year": yyyy,
            "month": mm,
            "day": dd,
            "start_date": start_date,
            "end_date": end_date,
        }

        params_cfg = self.provider.get("params") or {}
        if isinstance(params_cfg, dict):
            api_key_env = params_cfg.get("api_key_env")
            if api_key_env and "api_key" not in template_vars:
                template_vars["api_key"] = os.getenv(str(api_key_env), "")

            access_key_env = params_cfg.get("access_key_env")
            if access_key_env and "access_key" not in template_vars:
                template_vars["access_key"] = os.getenv(str(access_key_env), "")

        url: str | None
        if is_google_drive:
            url = None
        else:
            try:
                url = url_template.format(**template_vars)
            except KeyError as exc:
                logger.error(
                    "Provider %s url_template missing placeholder: %s",
                    self.provider.get("name"),
                    exc,
                )
                return {"status": "error", "url": None}

        filename = f"{pair}_{date}.bin"
        if is_google_drive:
            filename = self._google_drive_output_filename(
                template_vars=template_vars, fallback=filename
            )

        save_path_template = self.provider.get("save_path")
        if not save_path_template:
            if artifact_type:
                save_path_template = f"data/raw/fx/{artifact_type}/{self.provider['name']}/{{pair}}/{{year}}/{{month}}/{{day}}"
            else:
                logger.error(
                    "Provider %s has no save_path and no artifact_type", self.provider.get("name")
                )
                return {"status": "error", "url": url}

        save_prefix = save_path_template.format(**template_vars)
        local_dir = Path(self.base_data_dir) / save_prefix
        ensure_dir(local_dir)

        method = self.provider.get("method", "GET").upper()
        headers = self._prepare_headers()
        auth = self._prepare_auth()
        params: dict[str, str] = {}
        if isinstance(params_cfg, dict):
            for key, value in params_cfg.items():
                if key.endswith("_env"):
                    continue
                if isinstance(value, str):
                    params[key] = value.format(**template_vars)

        # Query API key auth support (legacy providers_single_pair.yaml)
        auth_cfg = self.provider.get("auth", {}) or {}
        if isinstance(auth_cfg, dict) and auth_cfg.get("type") == "query_api_key":
            api_key_env = auth_cfg.get("api_key_env")
            key_name = auth_cfg.get("key_param_name")
            if not key_name:
                # common fallbacks
                key_name = "apikey"
            if api_key_env:
                api_key_value = os.getenv(str(api_key_env), "")
                if api_key_value:
                    params[str(key_name)] = api_key_value

        # ---------------------------------------------------------
        # FETCH
        # ---------------------------------------------------------
        try:
            if is_google_drive:
                url, content = await self._fetch_google_drive_bytes(
                    pair=pair, day=day, template_vars=template_vars
                )
            else:
                async with aiohttp.ClientSession() as session:
                    _resp, content = await self._fetch(
                        session, method, url, params=params, headers=headers, auth=auth
                    )
        except Exception as e:
            if isinstance(e, RetryError):
                root = e.last_attempt.exception()
                if root is not None:
                    e = root
            http_status = getattr(e, "status", None)
            logger.error(f"[{pair}] Failed {url or '(google_drive)'} → {e}")
            if artifact_type and hasattr(self.db, "record_failure"):
                await self.db.record_failure(
                    provider=str(self.provider["name"]),
                    pair=pair,
                    date=date,
                    artifact_type=str(artifact_type),
                    url=url,
                    http_status=http_status,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
            return {"status": "error", "url": url}

        checksum = hashlib.sha256(content).hexdigest()

        provider_key = (
            f"{self.provider['name']}#{artifact_type}#{pair}"
            if artifact_type
            else f"{self.provider['name']}#{pair}"
        )
        if await self.db.exists_checksum(provider_key, checksum):
            logger.info(f"✓ [{pair}] Already downloaded for {dd}-{mm}-{yyyy}")
            return {"status": "skipped"}

        # ---------------------------------------------------------
        # MULTI-PAIR S3 KEY
        # ---------------------------------------------------------
        s3_key = f"{save_prefix}/{filename}".replace("\\", "/")

        # Write local raw file for on-disk acceptance checks.
        local_file = local_dir / filename
        local_file.write_bytes(content)

        await self.s3.upload_file(
            content=content, key=s3_key, content_type=guess_content_type(url, filename)
        )

        # Sidecar metadata
        repo_root = Path(__file__).resolve().parents[2]
        sidecar = build_sidecar_metadata(
            repo_root=repo_root,
            provider=str(self.provider["name"]),
            artifact_type=str(artifact_type) if artifact_type else None,
            pair=pair,
            date=date,
            url=url,
            http_method=method,
            request_headers={k: str(v) for k, v in headers.items()},
            raw_sha256=checksum,
            s3_bucket=S3_BUCKET,
            s3_key=s3_key,
            local_path=str(local_file),
        )
        sidecar_bytes = (json.dumps(sidecar, indent=2, sort_keys=True) + "\n").encode("utf-8")
        sidecar_key = f"{s3_key}.metadata.json"
        await self.s3.upload_file(
            content=sidecar_bytes, key=sidecar_key, content_type="application/json"
        )

        # Write local sidecar and update manifest.
        (local_dir / f"{filename}.metadata.json").write_bytes(sidecar_bytes)
        try:
            update_rollup_manifest(repo_root, sidecar)
        except Exception as exc:
            logger.warning("Failed to update rollup manifest: %s", exc)

        await self.db.add_download(provider_key, url, checksum, s3_key)
        if artifact_type and hasattr(self.db, "clear_failure"):
            await self.db.clear_failure(
                provider=str(self.provider["name"]),
                pair=pair,
                date=date,
                artifact_type=str(artifact_type),
            )
        logger.info(f"📤 Uploaded to s3://{S3_BUCKET}/{s3_key}")

        await self.indexer.index_file(
            provider=self.provider["name"],
            pair=pair,
            date=date,
            s3_key=s3_key,
            artifact_type=str(artifact_type) if artifact_type else None,
        )

        return {"status": "uploaded", "pair": pair, "key": s3_key}

    @staticmethod
    def _is_google_drive_provider(provider: Dict[str, Any]) -> bool:
        source = str(provider.get("source") or provider.get("protocol") or "").lower().strip()
        return source in {"google_drive", "gdrive", "google-drive"}

    def _google_drive_granularity(self) -> str:
        cfg = self.provider.get("google_drive") or {}
        if isinstance(cfg, dict):
            g = str(cfg.get("granularity") or "").lower().strip()
            if g:
                return g
        return "day"

    def _google_drive_output_filename(self, *, template_vars: dict[str, str], fallback: str) -> str:
        cfg = self.provider.get("google_drive") or {}
        if not isinstance(cfg, dict):
            return fallback

        out = cfg.get("output_filename_template")
        if isinstance(out, str) and out.strip():
            return out.format(**template_vars)

        # If we are extracting a CSV from a zip, default output to .csv for readability.
        extract_csv = bool(cfg.get("extract_csv", False))
        if extract_csv:
            stem = fallback.rsplit(".", 1)[0]
            return f"{stem}.csv"

        return fallback

    @retry(
        retry=retry_if_exception(lambda exc: not isinstance(exc, FileNotFoundError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=2, max=30),
    )
    async def _fetch_google_drive_bytes(
        self, *, pair: str, day: datetime, template_vars: dict[str, str]
    ) -> tuple[str, bytes]:
        """Resolve and download a Google Drive file as bytes.

        Expected provider schema:
        - source: google_drive
        - google_drive: {
            root_folder_id: str (or folder_id)
            subfolder_name_template?: str
            file_name_template?: str
            file_id_template?: str
          }
        - auth.type: google_drive_service_account | google_drive_authorized_user
        """

        gcfg = self.provider.get("google_drive") or {}
        if not isinstance(gcfg, dict):
            raise ValueError("google_drive config must be a mapping")

        root_folder_id = str(gcfg.get("root_folder_id") or gcfg.get("folder_id") or "").strip()
        root_folder_name = str(gcfg.get("root_folder_name") or "").strip()

        file_id_template = gcfg.get("file_id_template")
        file_name_template = gcfg.get("file_name_template")
        subfolder_name_template = gcfg.get("subfolder_name_template")

        repo_root = Path(__file__).resolve().parents[2]

        # Lazy import keeps non-gdrive workflows unchanged.
        from qf_downloader.google_drive_client import GoogleDriveClient

        client = GoogleDriveClient.from_provider(provider=self.provider, repo_root=repo_root)

        if not root_folder_id:
            if not root_folder_name:
                raise ValueError(
                    "google_drive.root_folder_id (or folder_id) is required unless root_folder_name is provided"
                )
            resolved = await asyncio.to_thread(
                client.find_folder_id_by_name, folder_name=root_folder_name
            )
            if not resolved:
                raise FileNotFoundError(f"Drive folder '{root_folder_name}' not found")
            root_folder_id = resolved

        if isinstance(file_id_template, str) and file_id_template.strip():
            file_id = file_id_template.format(**template_vars)
            url = f"gdrive://{file_id}"
            content = await asyncio.to_thread(client.download_file_bytes, file_id=file_id)
            extract_csv = bool(gcfg.get("extract_csv", False))
            if extract_csv:
                content = _extract_first_csv_from_zip_bytes(content)
            return url, content

        if not isinstance(file_name_template, str) or not file_name_template.strip():
            raise ValueError(
                "google_drive.file_name_template is required when file_id_template is not provided"
            )

        target_folder_id = root_folder_id
        if isinstance(subfolder_name_template, str) and subfolder_name_template.strip():
            subfolder_name = subfolder_name_template.format(**template_vars)
            resolved = await asyncio.to_thread(
                client.find_child_folder_id,
                parent_folder_id=root_folder_id,
                folder_name=subfolder_name,
            )
            if not resolved:
                raise FileNotFoundError(
                    f"Drive subfolder '{subfolder_name}' not found under root folder id={root_folder_id}"
                )
            target_folder_id = resolved

        filename = file_name_template.format(**template_vars)
        file_id = await asyncio.to_thread(
            client.find_file_id_by_name,
            folder_id=target_folder_id,
            filename=filename,
        )
        if not file_id:
            raise FileNotFoundError(
                f"Drive file '{filename}' not found in folder id={target_folder_id}"
            )

        url = f"gdrive://{file_id}"
        content = await asyncio.to_thread(client.download_file_bytes, file_id=file_id)
        extract_csv = bool(gcfg.get("extract_csv", False))
        if extract_csv:
            content = _extract_first_csv_from_zip_bytes(content)
        return url, content

    @staticmethod
    def _split_pair(pair: str) -> Tuple[str, str]:
        if pair.upper() == "ALL":
            return "", ""
        if "/" in pair:
            base, quote = pair.split("/", 1)
            return base, quote
        if len(pair) == 6:
            return pair[:3], pair[3:]
        raise ValueError(f"Unsupported pair format: {pair}")

    # ---------------------------------------------------------
    # HTTP CLIENT + HELPERS
    # ---------------------------------------------------------
    def _prepare_headers(self):
        h = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        }
        auth_cfg = self.provider.get("auth", {}) or {}
        if auth_cfg.get("type") == "header_api_key":
            key = os.getenv(auth_cfg.get("header_env"))
            if key:
                h[auth_cfg.get("header_name", "x-api-key")] = key
        return h

    def _prepare_auth(self):
        auth_cfg = self.provider.get("auth", {}) or {}
        if auth_cfg.get("type") == "basic":
            user = os.getenv(auth_cfg.get("user_env"))
            pw = os.getenv(auth_cfg.get("pass_env"))
            if user and pw:
                return aiohttp.BasicAuth(user, pw)
        return None

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=2, max=30),
    )
    async def _fetch(self, session, method, url, params, headers, auth):
        logger.info(f"Fetching {url}")
        async with session.request(method, url, params=params, headers=headers, auth=auth) as resp:
            resp.raise_for_status()
            content = await resp.read()
            return resp, content


def _extract_first_csv_from_zip_bytes(zip_bytes: bytes) -> bytes:
    import zipfile
    from io import BytesIO

    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise FileNotFoundError("No .csv file found inside zip")
        # Use the first CSV; vendor zips are typically single-file.
        with zf.open(csv_names[0]) as fp:
            return fp.read()
