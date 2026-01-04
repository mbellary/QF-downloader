import hashlib
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import aiohttp
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from qf_downloader.config import S3_BUCKET
from qf_downloader.db import DownloadDB
from qf_downloader.logger import get_logger
from qf_downloader.storage import S3Client
from qf_downloader.utils import ensure_dir, guess_content_type

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

        url_template = self.provider.get("url_template")
        if not url_template:
            logger.error(f"Provider {self.provider['name']} has no url_template")
            return

        url = url_template.format(pair=pair, year=yyyy, month=mm, day=dd)

        filename = f"{pair}_{yyyy}{mm}{dd}.bin"
        local_dir = Path(self.base_data_dir) / self.provider["save_path"].format(
            pair=pair, year=yyyy, month=mm, day=dd
        )
        ensure_dir(local_dir)

        method = self.provider.get("method", "GET").upper()
        headers = self._prepare_headers()
        auth = self._prepare_auth()
        params = {}  # no query params for Dukascopy

        # ---------------------------------------------------------
        # FETCH
        # ---------------------------------------------------------
        async with aiohttp.ClientSession() as session:
            try:
                resp, content = await self._fetch(
                    session, method, url, params=params, headers=headers, auth=auth
                )
            except Exception as e:
                logger.error(f"[{pair}] Failed {url} → {e}")
                return {"status": "error", "url": url}

        checksum = hashlib.sha256(content).hexdigest()

        provider_key = f"{self.provider['name']}_{pair}"
        if await self.db.exists_checksum(provider_key, checksum):
            logger.info(f"✓ [{pair}] Already downloaded for {dd}-{mm}-{yyyy}")
            return {"status": "skipped"}

        # ---------------------------------------------------------
        # MULTI-PAIR S3 KEY
        # ---------------------------------------------------------
        s3_key = (
            self.provider["save_path"].format(pair=pair, year=yyyy, month=mm, day=dd)
            + f"/{filename}"
        )

        await self.s3.upload_file(
            content=content, key=s3_key, content_type=guess_content_type(url, filename)
        )

        await self.db.add_download(provider_key, url, checksum, s3_key)
        logger.info(f"📤 Uploaded to s3://{S3_BUCKET}/{s3_key}")

        await self.indexer.index_file(
            provider=self.provider["name"], pair=pair, date=f"{yyyy}{mm}{dd}", s3_key=s3_key
        )

        return {"status": "uploaded", "pair": pair, "key": s3_key}

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
