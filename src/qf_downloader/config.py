import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from qf_downloader.logger import get_logger

logger = get_logger("downloader_worker.config")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR = BASE_DIR / "config" / "vendors"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

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
DB_PATH = DATA_DIR / _env("DB_FILE", "downloads.db")
PROVIDERS_FILE = CONFIG_DIR / _env("PROVIDERS_FILE", "fx_providers.json")
MACRO_FEEDS_FILE = CONFIG_DIR / _env("MACRO_FEEDS_FILE", "macro_feeds.json")
MACRO_PROVIDERS_FILE = CONFIG_DIR / _env("MACRO_PROVIDERS_FILE", "macro_providers.json")
NEWS_SECRETS_FILE = BASE_DIR / "config" / "secrets" / _env("NEWS_SECRETS_FILE", "news_api.json")
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
        dp = Path(_env("DOWNLOAD_PATH", str(DATA_DIR)))
        dp.mkdir(parents=True, exist_ok=True)
        self.download_path = dp


# if __name__ == "__main__":
#     print(CONFIG_DIR)
#     print(PROVIDERS_FILE)
