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

# aioboto3 session
_session = aioboto3.Session(region_name=AWS_REGION)
_boto3_session = boto3.session.Session(region_name=AWS_REGION)


def get_boto3_client(service):
    if APP_ENV == "localstack":
        # LocalStack setup
        logger.info(f"Initializing client {service} locally")
        return boto3.client(
            service,
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=LOCALSTACK_URL,
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
            return boto3.client(service, region_name=AWS_REGION)


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
    if APP_ENV == "localstack":
        # LocalStack setup
        logger.info(f"Initializing client {service} locally")
        return _session.client(
            service,
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            endpoint_url=LOCALSTACK_URL,
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
            profile_session = aioboto3.Session(region_name=AWS_REGION, profile_name=aws_profile)
            return profile_session.client(service)
        else:
            # No profile → IAM Role will be used (via metadata service)
            logger.info(f"Initializing client {service} in production using IAM Role")
            return _session.client(service, region_name=AWS_REGION)
