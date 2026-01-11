import hashlib
import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from qf_downloader.db import DownloadDB
from qf_downloader.logger import get_logger
from qf_downloader.storage import S3Client
from qf_downloader.utils import ensure_dir, guess_content_type

from .metadata import build_macro_news_sidecar_metadata, update_rollup_manifest_macro_news

logger = get_logger("downloader.exogenous")


def validate_end_date_not_forward_looking(*, end: date, now: datetime | None = None) -> None:
    """Validate that the requested end date is not forward-looking.

    Phase 0.2 rule: default ingestion should only include complete prior UTC days.
    """

    effective_now = now or datetime.now(UTC)
    yesterday_utc = effective_now.date() - timedelta(days=1)
    if end > yesterday_utc:
        raise ValueError(
            f"forward-looking end date is not allowed: end={end.isoformat()} "
            f"(max={yesterday_utc.isoformat()})"
        )


class ExogenousProviderDownloader:
    """Downloader for Phase 0.2 exogenous (macro/news) providers.

    Unlike `ProviderDownloader`, Phase 0.2 artifacts are partitioned by UTC day
    without an FX-pair dimension.
    """

    def __init__(
        self,
        *,
        provider: dict[str, Any],
        s3: S3Client,
        db: DownloadDB,
        base_data_dir: str = "./data",
    ) -> None:
        self.provider = provider
        self.s3 = s3
        self.db = db
        self.base_data_dir = base_data_dir

    async def backfill_range(self, *, start: datetime, end: datetime) -> None:
        day = start
        while day <= end:
            await self._download_single_day(day=day)
            day += timedelta(days=1)

    async def _download_single_day(self, *, day: datetime) -> dict[str, Any]:
        yyyy = day.strftime("%Y")
        mm = day.strftime("%m")
        dd = day.strftime("%d")
        yyyymmdd = f"{yyyy}{mm}{dd}"

        artifact_type = str(
            self.provider.get("artifact_type") or self.provider.get("type") or ""
        ).lower()
        provider_name = str(self.provider.get("name"))

        url_template = self.provider.get("url_template")
        if not url_template:
            logger.error("Provider %s has no url_template", provider_name)
            return {"status": "error", "url": None}

        template_vars: dict[str, str] = {
            "year": yyyy,
            "month": mm,
            "day": dd,
            "date": yyyymmdd,
            "start_date": day.strftime("%Y-%m-%d"),
            "end_date": day.strftime("%Y-%m-%d"),
        }

        params_cfg = self.provider.get("params") or {}
        if isinstance(params_cfg, dict):
            api_key_env = params_cfg.get("api_key_env")
            if api_key_env and "api_key" not in template_vars:
                template_vars["api_key"] = os.getenv(str(api_key_env), "")

            access_key_env = params_cfg.get("access_key_env")
            if access_key_env and "access_key" not in template_vars:
                template_vars["access_key"] = os.getenv(str(access_key_env), "")

        try:
            url = str(url_template).format(**template_vars)
        except KeyError as exc:
            logger.error("Provider %s url_template missing placeholder: %s", provider_name, exc)
            return {"status": "error", "url": None}

        filename = self._default_filename(artifact_type=artifact_type, yyyymmdd=yyyymmdd)

        save_path_template = self.provider.get("save_path")
        if not save_path_template:
            save_prefix = self._default_save_prefix(
                artifact_type=artifact_type,
                provider=provider_name,
                yyyy=yyyy,
                mm=mm,
                dd=dd,
            )
        else:
            save_prefix = str(save_path_template).format(
                provider=provider_name,
                artifact_type=artifact_type,
                **template_vars,
            )

        local_dir = Path(self.base_data_dir) / save_prefix
        ensure_dir(local_dir)

        method = str(self.provider.get("method", "GET")).upper()
        headers = self._prepare_headers()
        auth = self._prepare_auth()
        params: dict[str, str] = {}
        if isinstance(params_cfg, dict):
            for key, value in params_cfg.items():
                if key.endswith("_env"):
                    continue
                if isinstance(value, str):
                    params[key] = value.format(**template_vars)

        # Query API key auth support (legacy pattern)
        auth_cfg = self.provider.get("auth", {}) or {}
        if isinstance(auth_cfg, dict) and auth_cfg.get("type") == "query_api_key":
            api_key_env = auth_cfg.get("api_key_env")
            key_name = auth_cfg.get("key_param_name") or "apikey"
            if api_key_env:
                api_key_value = os.getenv(str(api_key_env), "")
                if api_key_value:
                    params[str(key_name)] = api_key_value

        async with aiohttp.ClientSession() as session:
            try:
                _resp, content = await self._fetch(
                    session, method, url, params=params, headers=headers, auth=auth
                )
            except Exception as exc:
                http_status = getattr(exc, "status", None)
                logger.error("Failed %s -> %s", url, exc)
                if hasattr(self.db, "record_failure"):
                    await self.db.record_failure(
                        provider=provider_name,
                        pair="__EXOGENOUS__",
                        date=yyyymmdd,
                        artifact_type=artifact_type,
                        url=url,
                        http_status=http_status,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                return {"status": "error", "url": url}

        checksum = hashlib.sha256(content).hexdigest()

        provider_key = f"{provider_name}#{artifact_type}#{yyyymmdd}"
        if await self.db.exists_checksum(provider_key, checksum):
            logger.info("✓ [%s] Already ingested for %s", provider_name, yyyymmdd)
            return {"status": "skipped"}

        s3_key = f"{save_prefix}/{filename}".replace("\\", "/")

        local_file = local_dir / filename
        local_file.write_bytes(content)

        await self.s3.upload_file(
            content=content,
            key=s3_key,
            content_type=guess_content_type(url, filename),
        )

        repo_root = Path(__file__).resolve().parents[2]
        sidecar = build_macro_news_sidecar_metadata(
            repo_root=repo_root,
            provider=provider_name,
            artifact_type=artifact_type,
            partition_date_utc=day.date().isoformat(),
            url=url,
            http_method=method,
            request_headers={k: str(v) for k, v in headers.items()},
            raw_sha256=checksum,
            s3_bucket=getattr(self.s3, "bucket", None),
            s3_key=s3_key,
            local_path=str(local_file),
        )
        sidecar_bytes = (json.dumps(sidecar, indent=2, sort_keys=True) + "\n").encode("utf-8")
        sidecar_key = f"{s3_key}.metadata.json"
        await self.s3.upload_file(
            content=sidecar_bytes,
            key=sidecar_key,
            content_type="application/json",
        )

        (local_dir / f"{filename}.metadata.json").write_bytes(sidecar_bytes)
        try:
            update_rollup_manifest_macro_news(repo_root, sidecar)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to update macro/news rollup manifest: %s", exc)

        await self.db.add_download(provider_key, url, checksum, s3_key)
        if hasattr(self.db, "clear_failure"):
            await self.db.clear_failure(
                provider=provider_name,
                pair="__EXOGENOUS__",
                date=yyyymmdd,
                artifact_type=artifact_type,
            )

        return {"status": "uploaded", "key": s3_key}

    @staticmethod
    def _default_save_prefix(
        *, artifact_type: str, provider: str, yyyy: str, mm: str, dd: str
    ) -> str:
        if artifact_type == "macro_events":
            return f"data/raw/macro/events/{provider}/{yyyy}/{mm}/{dd}"
        if artifact_type == "news":
            return f"data/raw/news/{provider}/{yyyy}/{mm}/{dd}"
        raise ValueError(f"Unsupported artifact_type for Phase 0.2: {artifact_type}")

    @staticmethod
    def _default_filename(*, artifact_type: str, yyyymmdd: str) -> str:
        if artifact_type == "macro_events":
            return f"macro_events_{yyyymmdd}.json"
        if artifact_type == "news":
            return f"news_{yyyymmdd}.json"
        raise ValueError(f"Unsupported artifact_type for Phase 0.2: {artifact_type}")

    def _prepare_headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        }
        auth_cfg = self.provider.get("auth", {}) or {}
        if isinstance(auth_cfg, dict) and auth_cfg.get("type") == "header_api_key":
            key = os.getenv(str(auth_cfg.get("header_env")))
            if key:
                h[str(auth_cfg.get("header_name", "x-api-key"))] = key
        return h

    def _prepare_auth(self) -> aiohttp.BasicAuth | None:
        auth_cfg = self.provider.get("auth", {}) or {}
        if isinstance(auth_cfg, dict) and auth_cfg.get("type") == "basic":
            user = os.getenv(str(auth_cfg.get("user_env")))
            pw = os.getenv(str(auth_cfg.get("pass_env")))
            if user and pw:
                return aiohttp.BasicAuth(user, pw)
        return None

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(5),
        wait=wait_exponential(min=2, max=30),
    )
    async def _fetch(self, session, method, url, params, headers, auth):
        logger.info("Fetching %s", url)
        async with session.request(method, url, params=params, headers=headers, auth=auth) as resp:
            resp.raise_for_status()
            content = await resp.read()
            return resp, content
