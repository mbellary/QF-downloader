import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import boto3
import pytest

exogenous = pytest.importorskip(
    "qf_downloader.exogenous_downloader",
    reason="Phase 0.2 exogenous downloader not implemented yet",
)

ExogenousProviderDownloader = exogenous.ExogenousProviderDownloader


@pytest.mark.docker
def test_p0_2_macro_events_ingestion_uploads_raw_and_sidecar_to_s3(
    localstack_resources, tmp_path
) -> None:
    """Phase 0.2 integration contract (S3).

    Encodes intended Phase 0.2 behavior once implemented:
    - ExogenousProviderDownloader uploads raw macro_events artifact to S3 at deterministic key.
    - Uploads sidecar metadata JSON at `<raw_key>.metadata.json`.

    Notes:
    - Stubs HTTP fetch to avoid network.
    - Skipped until `qf_downloader.exogenous_downloader` exists.
    """

    # Import after localstack_env has reloaded config.
    from qf_downloader.config import (
        AWS_ACCESS_KEY_ID,
        AWS_REGION,
        AWS_SECRET_ACCESS_KEY,
        S3_BUCKET,
    )
    from qf_downloader.db import DownloadDB
    from qf_downloader.storage import S3Client

    endpoint_url = localstack_resources["endpoint_url"]

    provider_name = "FRED"
    artifact_type = "macro_events"
    day = datetime(2024, 1, 2, tzinfo=UTC)

    yyyy, mm, dd = "2024", "01", "02"
    filename = "macro_events_20240102.json"

    provider = {
        "name": provider_name,
        "artifact_type": artifact_type,
        "url_template": "https://example.invalid/{year}/{month}/{day}.json",
        # Intentionally omit save_path: implementation should use deterministic default.
    }

    db_path = tmp_path / "downloads.db"
    db = DownloadDB(str(db_path))

    s3 = S3Client(
        bucket=S3_BUCKET,
        aws_key=AWS_ACCESS_KEY_ID,
        aws_secret=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
    )

    dl = ExogenousProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))

    # Stub network fetch.
    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    async def scenario() -> dict:
        await db.init()
        try:
            return await dl._download_single_day(day=day)
        finally:
            await db.close()

    result = asyncio.run(scenario())
    assert result["status"] in {"uploaded", "skipped"}

    raw_key = f"data/raw/macro/events/{provider_name}/{yyyy}/{mm}/{dd}/{filename}"
    sidecar_key = f"{raw_key}.metadata.json"

    s3_boto = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=endpoint_url,
    )

    # Assert raw object exists.
    s3_boto.head_object(Bucket=S3_BUCKET, Key=raw_key)

    # Assert sidecar exists and is parseable JSON with the expected schema id.
    obj = s3_boto.get_object(Bucket=S3_BUCKET, Key=sidecar_key)
    sidecar = json.loads(obj["Body"].read().decode("utf-8"))
    assert sidecar["schema_id"] == "infra.phase0.macro_news_ingestion"


@pytest.mark.docker
def test_p0_2_news_ingestion_uploads_raw_and_sidecar_to_s3(localstack_resources, tmp_path) -> None:
    """Phase 0.2 integration contract (S3) for news.

    Encodes intended Phase 0.2 behavior once implemented:
    - ExogenousProviderDownloader uploads raw news artifact to S3 at deterministic key.
    - Uploads sidecar metadata JSON at `<raw_key>.metadata.json`.

    Notes:
    - Stubs HTTP fetch to avoid network.
    - Skipped until `qf_downloader.exogenous_downloader` exists.
    """

    # Import after localstack_env has reloaded config.
    from qf_downloader.config import (
        AWS_ACCESS_KEY_ID,
        AWS_REGION,
        AWS_SECRET_ACCESS_KEY,
        S3_BUCKET,
    )
    from qf_downloader.db import DownloadDB
    from qf_downloader.storage import S3Client

    endpoint_url = localstack_resources["endpoint_url"]

    provider_name = "fmp"
    artifact_type = "news"
    day = datetime(2024, 1, 2, tzinfo=UTC)

    yyyy, mm, dd = "2024", "01", "02"
    filename = "news_20240102.json"

    provider = {
        "name": provider_name,
        "artifact_type": artifact_type,
        "url_template": "https://example.invalid/{year}/{month}/{day}.json",
        # Intentionally omit save_path: implementation should use deterministic default.
    }

    db_path = tmp_path / "downloads.db"
    db = DownloadDB(str(db_path))

    s3 = S3Client(
        bucket=S3_BUCKET,
        aws_key=AWS_ACCESS_KEY_ID,
        aws_secret=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
    )

    dl = ExogenousProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))

    # Stub network fetch.
    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    async def scenario() -> dict:
        await db.init()
        try:
            return await dl._download_single_day(day=day)
        finally:
            await db.close()

    result = asyncio.run(scenario())
    assert result["status"] in {"uploaded", "skipped"}

    raw_key = f"data/raw/news/{provider_name}/{yyyy}/{mm}/{dd}/{filename}"
    sidecar_key = f"{raw_key}.metadata.json"

    s3_boto = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=endpoint_url,
    )

    # Assert raw object exists.
    s3_boto.head_object(Bucket=S3_BUCKET, Key=raw_key)

    # Assert sidecar exists and is parseable JSON with the expected schema id.
    obj = s3_boto.get_object(Bucket=S3_BUCKET, Key=sidecar_key)
    sidecar = json.loads(obj["Body"].read().decode("utf-8"))
    assert sidecar["schema_id"] == "infra.phase0.macro_news_ingestion"
