import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from qf_downloader.logger import get_logger

logger = get_logger("downloader_worker.config")

PACKAGE_DIR = Path(__file__).resolve().parent


APP_ENV = os.getenv("APP_ENV", "production").lower()


if APP_ENV == "localstack":
    load_dotenv(PACKAGE_DIR / ".env.dev")
    logger.info("Loaded localstack environment variables")
else:
    load_dotenv(PACKAGE_DIR / ".env.prod")
    logger.info("Loaded production environment variables")


def _env(name, default=None):
    v = os.getenv(name)
    return v if v is not None else default


LOCALSTACK_URL = _env("LOCALSTACK_URL", None)  # if use_localstack else None


S3_BUCKET = _env("S3_BUCKET", None)
AWS_ACCESS_KEY_ID = _env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = _env("AWS_SECRET_ACCESS_KEY")
AWS_REGION = _env("AWS_REGION", "us-east-1")
RAW_FILE_INDEX_TABLE = _env("RAW_FILE_INDEX_TABLE", "us-east-1")
DB_PATH = _env("DB_PATH", "./data/downloads.db")
PROVIDERS_FILE = _env("PROVIDERS_FILE", "./src/example_pkg/providers.yaml")
POLL_INTERVAL_SECONDS = int(_env("POLL_INTERVAL_SECONDS", "300"))
TWELVEDATA_API_KEY = _env("TWELVEDATA_API_KEY")
FMP_API_KEY = _env("FMP_API_KEY")
FRED_API_KEY = _env("FRED_API_KEY")
FX_API_KEY = _env("FX_API_KEY")

START_DATE = _env("START_DATE", "")
END_DATE = _env("END_DATE", "")


@dataclass
class Settings:
    """Minimal settings object used by tests and runtime."""

    download_path: Path

    def __init__(self):
        dp = Path(_env("DOWNLOAD_PATH", "./data"))
        dp.mkdir(parents=True, exist_ok=True)
        self.download_path = dp
