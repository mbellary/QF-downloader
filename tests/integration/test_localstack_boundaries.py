import asyncio
from uuid import uuid4

import pytest


@pytest.mark.docker
def test_s3client_upload_and_exists(localstack_resources) -> None:
    # Import after localstack_env has reloaded config.
    from qf_downloader.config import AWS_ACCESS_KEY_ID, AWS_REGION, AWS_SECRET_ACCESS_KEY, S3_BUCKET
    from qf_downloader.storage import S3Client

    s3 = S3Client(
        bucket=S3_BUCKET,
        aws_key=AWS_ACCESS_KEY_ID,
        aws_secret=AWS_SECRET_ACCESS_KEY,
        region=AWS_REGION,
    )

    key = f"tests/{uuid4().hex}.bin"
    payload = b"hello-localstack"

    async def scenario() -> bool:
        await s3.upload_file(content=payload, key=key, content_type="application/octet-stream")
        return await s3.object_exists(key)

    assert asyncio.run(scenario()) is True


@pytest.mark.docker
def test_dynamodb_roundtrip_via_boto3_client(localstack_resources) -> None:
    # Validate that our helper returns a working DynamoDB client against LocalStack.
    from qf_downloader.aws_clients import get_boto3_client
    from qf_downloader.config import RAW_FILE_INDEX_TABLE

    client = get_boto3_client("dynamodb")

    pk = "EURUSD#dukascopy"
    sk = f"20240101#tests/{uuid4().hex}.bin"

    client.put_item(
        TableName=RAW_FILE_INDEX_TABLE,
        Item={
            "pk": {"S": pk},
            "sk": {"S": sk},
            "provider": {"S": "dukascopy"},
            "pair": {"S": "EURUSD"},
            "date": {"S": "20240101"},
            "s3_key": {"S": sk.split("#", 1)[1]},
            "state": {"S": "PENDING"},
        },
    )

    resp = client.get_item(
        TableName=RAW_FILE_INDEX_TABLE,
        Key={"pk": {"S": pk}, "sk": {"S": sk}},
        ConsistentRead=True,
    )

    assert resp.get("Item") is not None


@pytest.mark.docker
@pytest.mark.xfail(
    reason="S3Indexer currently treats an aioboto3 client as a resource (Table()), which is incompatible.",
    strict=False,
)
def test_s3indexer_index_and_query(localstack_resources) -> None:
    # This is the intended integration contract once S3Indexer is corrected.
    from qf_downloader.s3_indexer import S3Indexer

    indexer = S3Indexer()

    async def scenario() -> list[str]:
        await indexer.index_file(
            provider="dukascopy",
            pair="EURUSD",
            date="20240101",
            s3_key=f"tests/{uuid4().hex}.bin",
        )
        return await indexer.query_keys(
            provider="dukascopy",
            pair="EURUSD",
            start_date="20240101",
            end_date="20240101",
        )

    keys = asyncio.run(scenario())
    assert len(keys) == 1
