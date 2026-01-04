import os

import aioboto3
import boto3

from qf_downloader.config import (
    APP_ENV,
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    LOCALSTACK_URL,
)
from qf_downloader.logger import get_logger

logger = get_logger("data_transformer.clients")


def _runtime_config() -> tuple[str, str | None, str, str | None, str | None]:
    """Resolve runtime AWS configuration.

    Important: config values can be stale if modules are imported before tests
    mutate environment variables. Prefer environment variables at call time.
    """

    app_env = (os.getenv("APP_ENV") or APP_ENV or "production").lower()
    localstack_url = os.getenv("LOCALSTACK_URL") or LOCALSTACK_URL
    region = os.getenv("AWS_REGION") or AWS_REGION
    access_key = os.getenv("AWS_ACCESS_KEY_ID") or AWS_ACCESS_KEY_ID
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or AWS_SECRET_ACCESS_KEY
    return app_env, localstack_url, region, access_key, secret_key


def get_boto3_client(service):
    app_env, localstack_url, region, access_key, secret_key = _runtime_config()

    if app_env == "localstack":
        # LocalStack setup
        logger.info(f"Initializing client {service} locally")
        return boto3.client(
            service,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=localstack_url,
        )
    else:
        # Production: use IAM Role if available
        # If AWS_PROFILE is set, boto3 will use it.
        # If not, it will fall back to the IAM Role automatically.
        # Ensure no accidental env creds are used in production
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)

        logger.info(f"Initializing client {service} in production")
        aws_profile = os.getenv("AWS_PROFILE")
        if aws_profile:
            logger.info(
                f"Initializing client {service} in production using AWS_PROFILE {aws_profile}"
            )
            session = boto3.Session(profile_name=aws_profile)
            return session.client(service)
        else:
            # No profile → IAM Role will be used (via metadata service)
            logger.info(f"Initializing client {service} in production using IAM Role")
            return boto3.client(service, region_name=region)


class AwsClientManager:
    """Lightweight manager used by integration tests to upload files to S3.

    This wraps boto3 client and provides `upload_to_s3(path, bucket, key)` which
    returns True on success.
    """

    def __init__(self, endpoint_url: str = None):
        self.endpoint_url = endpoint_url

    def _client(self):
        if self.endpoint_url:
            return boto3.client(
                "s3",
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                endpoint_url=self.endpoint_url,
            )
        return boto3.client("s3", region_name=AWS_REGION)

    def upload_to_s3(self, path: str, bucket: str, key: str) -> bool:
        client = self._client()
        try:
            client.upload_file(path, bucket, key)
            return True
        except Exception:
            return False


async def get_aboto3_client(service):
    app_env, localstack_url, region, access_key, secret_key = _runtime_config()

    if app_env == "localstack":
        # LocalStack setup
        logger.info(f"Initializing client {service} locally")
        session = aioboto3.Session(region_name=region)
        return session.client(
            service,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=localstack_url,
        )
    else:
        # Production: use IAM Role if available
        # If AWS_PROFILE is set, boto3 will use it.
        # If not, it will fall back to the IAM Role automatically.
        logger.info(f"Initializing client {service} in production")
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
        aws_profile = os.getenv("AWS_PROFILE")
        if aws_profile:
            logger.info(
                f"Initializing client {service} in production using AWS_PROFILE {aws_profile}"
            )
            profile_session = aioboto3.Session(region_name=region, profile_name=aws_profile)
            return profile_session.client(service)
        else:
            # No profile → IAM Role will be used (via metadata service)
            logger.info(f"Initializing client {service} in production using IAM Role")
            session = aioboto3.Session(region_name=region)
            return session.client(service, region_name=region)
