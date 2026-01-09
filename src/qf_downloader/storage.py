import os
from typing import Optional

import aioboto3

from qf_downloader.config import (
    APP_ENV,
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    LOCALSTACK_URL,
)
from qf_downloader.logger import get_logger

logger = get_logger("downloader.clients")


class S3Client:
    def __init__(self, bucket: str, aws_key: str, aws_secret: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.aws_key = aws_key
        self.aws_secret = aws_secret
        self.region = region
        self._session = aioboto3.Session()

    async def _get_client(self):
        service = "s3"
        if APP_ENV == "localstack":
            # LocalStack setup
            logger.info(f"Initializing client {service} locally")
            return self._session.client(
                service,
                region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                endpoint_url=LOCALSTACK_URL
            )
        else:
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
                return self._session.client(service)

    async def object_exists(self, key: str) -> bool:
        async with await self._get_client() as client:
            try:
                await client.head_object(Bucket=self.bucket, Key=key)
                return True
            except client.exceptions.ClientError:
                return False

    # async def upload_file(self, filepath: str, key: str, content_type: Optional[str] = None) -> str:
    #     async with await self._get_client() as client:
    #         extra = {}
    #         if content_type:
    #             extra['ContentType'] = content_type
    #         await client.upload_file(Filename=filepath, Bucket=self.bucket, Key=key, ExtraArgs=extra)
    #     return key

    async def upload_file(self, content, key: str, content_type: Optional[str] = None) -> str:
        async with await self._get_client() as client:
            extra = {}
            if content_type:
                extra["ContentType"] = content_type
            await client.put_object(
                Body=content, Bucket=self.bucket, Key=key, ContentType=content_type
            )
        return key


class LocalStorage:
    """Simple synchronous local storage used by unit tests."""

    def __init__(self, base_path: str = "."):
        self.base_path = base_path

    def write_file(self, name: str, content: bytes) -> str:
        path = os.path.join(self.base_path, name)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(content)
        return name

    def read_file(self, name: str) -> bytes:
        path = os.path.join(self.base_path, name)
        with open(path, "rb") as fh:
            return fh.read()
