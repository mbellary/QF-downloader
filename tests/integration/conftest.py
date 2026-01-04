import importlib
import os
import uuid
from urllib.parse import urlparse

import boto3
import pytest
from botocore.config import Config


def _default_localstack_url() -> str:
    # Host-mode default. Docker-mode should set LOCALSTACK_URL explicitly.
    return os.environ.get("LOCALSTACK_URL", "http://localhost:4566")


def _endpoint_hostport(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    return parsed.netloc


@pytest.fixture(scope="session")
def localstack_env():
    endpoint_url = _default_localstack_url()

    mp = pytest.MonkeyPatch()

    mp.setenv("APP_ENV", "localstack")
    mp.setenv("LOCALSTACK_URL", endpoint_url)
    mp.setenv("AWS_ACCESS_KEY_ID", os.environ.get("AWS_ACCESS_KEY_ID", "test"))
    mp.setenv("AWS_SECRET_ACCESS_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY", "test"))
    mp.setenv("AWS_REGION", os.environ.get("AWS_REGION", "us-east-1"))

    # Use unique resources per test session to avoid collisions.
    bucket = os.environ.get("S3_BUCKET") or f"qf-test-{uuid.uuid4().hex[:12]}"
    table = os.environ.get("RAW_FILE_INDEX_TABLE") or f"raw-file-index-{uuid.uuid4().hex[:12]}"

    mp.setenv("S3_BUCKET", bucket)
    mp.setenv("RAW_FILE_INDEX_TABLE", table)

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
        client_config = Config(connect_timeout=1, read_timeout=2, retries={"max_attempts": 1})
        s3 = boto3.client(
            "s3",
            region_name=os.environ["AWS_REGION"],
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            endpoint_url=endpoint_url,
            config=client_config,
        )
        s3.list_buckets()
    except Exception as exc:
        mp.undo()
        pytest.skip(
            "LocalStack is not reachable at "
            f"{endpoint_url} (hostport={_endpoint_hostport(endpoint_url)}): {exc}"
        )

    payload = {
        "endpoint_url": endpoint_url,
        "bucket": bucket,
        "table": table,
        "region": os.environ["AWS_REGION"],
    }

    yield payload

    mp.undo()


@pytest.fixture(scope="session")
def localstack_resources(localstack_env):
    endpoint_url = localstack_env["endpoint_url"]
    region = localstack_env["region"]
    bucket = localstack_env["bucket"]
    table = localstack_env["table"]

    client_config = Config(connect_timeout=1, read_timeout=5, retries={"max_attempts": 1})
    s3 = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        endpoint_url=endpoint_url,
        config=client_config,
    )
    dynamodb = boto3.client(
        "dynamodb",
        region_name=region,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        endpoint_url=endpoint_url,
        config=client_config,
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
