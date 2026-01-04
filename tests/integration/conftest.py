import importlib
import os
import uuid
from urllib.parse import urlparse

import boto3
import pytest


def _default_localstack_url() -> str:
    # Host-mode default. Docker-mode should set LOCALSTACK_URL explicitly.
    return os.environ.get("LOCALSTACK_URL", "http://localhost:4566")


def _endpoint_hostport(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    return parsed.netloc


@pytest.fixture(scope="session")
def localstack_env(monkeypatch):
    endpoint_url = _default_localstack_url()

    monkeypatch.setenv("APP_ENV", "localstack")
    monkeypatch.setenv("LOCALSTACK_URL", endpoint_url)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", os.environ.get("AWS_ACCESS_KEY_ID", "test"))
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY", "test"))
    monkeypatch.setenv("AWS_REGION", os.environ.get("AWS_REGION", "us-east-1"))

    # Use unique resources per test session to avoid collisions.
    bucket = os.environ.get("S3_BUCKET") or f"qf-test-{uuid.uuid4().hex[:12]}"
    table = os.environ.get("RAW_FILE_INDEX_TABLE") or f"raw-file-index-{uuid.uuid4().hex[:12]}"

    monkeypatch.setenv("S3_BUCKET", bucket)
    monkeypatch.setenv("RAW_FILE_INDEX_TABLE", table)

    # Reload config-dependent modules so they pick up the env vars set above.
    import qf_downloader.aws_clients as aws_clients
    import qf_downloader.config as config
    import qf_downloader.s3_indexer as s3_indexer
    import qf_downloader.storage as storage

    importlib.reload(config)
    importlib.reload(aws_clients)
    importlib.reload(storage)
    importlib.reload(s3_indexer)

    # Skip if LocalStack is not reachable.
    try:
        s3 = boto3.client(
            "s3",
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            endpoint_url=endpoint_url,
        )
        s3.list_buckets()
    except Exception as exc:
        pytest.skip(
            "LocalStack is not reachable at "
            f"{endpoint_url} (hostport={_endpoint_hostport(endpoint_url)}): {exc}"
        )

    return {
        "endpoint_url": endpoint_url,
        "bucket": bucket,
        "table": table,
        "region": os.environ["AWS_REGION"],
    }


@pytest.fixture(scope="session")
def localstack_resources(localstack_env):
    endpoint_url = localstack_env["endpoint_url"]
    region = localstack_env["region"]
    bucket = localstack_env["bucket"]
    table = localstack_env["table"]

    s3 = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        endpoint_url=endpoint_url,
    )
    dynamodb = boto3.client(
        "dynamodb",
        region_name=region,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        endpoint_url=endpoint_url,
    )

    # S3 bucket
    try:
        s3.create_bucket(Bucket=bucket)
    except Exception:
        # LocalStack may raise if the bucket already exists; treat as idempotent.
        pass

    # DynamoDB table
    try:
        dynamodb.create_table(
            TableName=table,
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName=table)
    except Exception:
        # Treat table provisioning as idempotent.
        pass

    return localstack_env
