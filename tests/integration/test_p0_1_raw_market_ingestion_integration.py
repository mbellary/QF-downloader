import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import boto3
import pytest


@pytest.mark.docker
def test_p0_1_ingestion_uploads_raw_and_sidecar_and_indexes_artifact_type(
    localstack_resources, tmp_path
) -> None:
    """Phase 0.1 integration contract.

    This test encodes the target behavior once Phase 0.1 is implemented:
    - ProviderDownloader uploads the raw artifact to S3 at a deterministic key.
    - ProviderDownloader uploads a sidecar metadata JSON at `<raw_key>.metadata.json`.
    - DynamoDB index entry exists for the raw artifact and includes `artifact_type`.

    Notes:
    - This test stubs HTTP fetch to avoid network and keep the test deterministic.
    - It is expected to fail until the Phase 0.1 implementation lands.
    """

    # Import after localstack_env has reloaded config.
    from qf_downloader.aws_clients import get_boto3_client
    from qf_downloader.config import (
        AWS_ACCESS_KEY_ID,
        AWS_REGION,
        AWS_SECRET_ACCESS_KEY,
        RAW_FILE_INDEX_TABLE,
        S3_BUCKET,
    )
    from qf_downloader.db import DownloadDB
    from qf_downloader.downloader import ProviderDownloader
    from qf_downloader.storage import S3Client

    endpoint_url = localstack_resources["endpoint_url"]

    provider_name = "dukascopy"
    artifact_type = "tick"
    pair = "EURUSD"
    day = datetime(2024, 1, 2, tzinfo=UTC)

    yyyy, mm, dd = "2024", "01", "02"
    date = f"{yyyy}{mm}{dd}"
    filename = f"{pair}_{date}.bin"

    # Use the Phase 0.1 deterministic layout (also used for S3 key prefix).
    save_path = f"data/raw/fx/{artifact_type}/{provider_name}/{{pair}}/{{year}}/{{month}}/{{day}}"

    provider = {
        "name": provider_name,
        "artifact_type": artifact_type,
        "supports_pairs": [pair],
        "save_path": save_path,
        "url_template": "https://example.invalid/{pair}/{year}/{month}/{day}.bin",
    }

    db_path = tmp_path / "downloads.db"
    db = DownloadDB(str(db_path))

    s3 = S3Client(
        bucket=S3_BUCKET,
        aws_key=AWS_ACCESS_KEY_ID,
        aws_secret=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
    )

    dl = ProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))

    # Stub network fetch.
    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    async def scenario() -> dict:
        await db.init()
        try:
            return await dl._download_single_day(pair=pair, day=day)
        finally:
            await db.close()

    result = asyncio.run(scenario())
    assert result["status"] in {"uploaded", "skipped"}

    raw_key = f"data/raw/fx/{artifact_type}/{provider_name}/{pair}/{yyyy}/{mm}/{dd}/{filename}"
    sidecar_key = f"{raw_key}.metadata.json"

    # Assert raw object exists.
    s3_boto = boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        endpoint_url=endpoint_url,
    )
    s3_boto.head_object(Bucket=S3_BUCKET, Key=raw_key)

    # Assert sidecar exists.
    s3_boto.head_object(Bucket=S3_BUCKET, Key=sidecar_key)

    # Assert DynamoDB index row exists and includes artifact_type.
    dynamo = get_boto3_client("dynamodb")

    expected_pk = f"{pair}#{provider_name}#{artifact_type}"
    expected_sk = f"{date}#{raw_key}"

    resp = dynamo.get_item(
        TableName=RAW_FILE_INDEX_TABLE,
        Key={"pk": {"S": expected_pk}, "sk": {"S": expected_sk}},
        ConsistentRead=True,
    )

    item = resp.get("Item")
    assert item is not None
    assert item.get("artifact_type", {}).get("S") == artifact_type
