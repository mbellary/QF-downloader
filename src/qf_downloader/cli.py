import asyncio
from datetime import datetime, timedelta

import click
import typer
import yaml

from .config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    DB_PATH,
    POLL_INTERVAL_SECONDS,
    PROVIDERS_FILE,
    S3_BUCKET,
)
from .db import DownloadDB
from .downloader import ProviderDownloader
from .logger import get_logger
from .storage import S3Client

logger = get_logger("downloader.cli")

app = typer.Typer(help="MT5 Multi-Pair Downloader CLI")

# Backwards-compatible CLI object expected by tests. Provide a lightweight
# click `Command` that responds to `--help`. Runtime can still use `app`.

cli = click.Command(name="qf_downloader")


# ----------------------------------------------------------
# LIST PROVIDERS
# ----------------------------------------------------------
@app.command()
def list_providers(providers_file: str = None):
    pf = providers_file or PROVIDERS_FILE
    with open(pf, "r") as fh:
        providers_cfg = yaml.safe_load(fh)

    print("\nAvailable Providers:\n")
    for p in providers_cfg.get("providers", []):
        print(
            f"- {p['name']}: supports_pairs={p.get('supports_pairs')}, "
            f"url_template={p.get('url_template')}"
        )


# ----------------------------------------------------------
# NORMAL RUNTIME POLLING LOOP (incremental updates)
# ----------------------------------------------------------
async def _run_loop(providers_cfg):
    db = DownloadDB(DB_PATH)
    await db.init()
    s3 = S3Client(S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)

    async def provider_poll(provider):
        dl = ProviderDownloader(provider, s3, db)
        interval = provider.get("poll_interval", POLL_INTERVAL_SECONDS)

        while True:
            try:
                await dl.download_and_upload()
                logger.info(f"Processed provider {provider['name']}")
            except Exception as e:
                logger.error(f"Provider {provider['name']} failed → {e}")

            await asyncio.sleep(interval)

    tasks = [asyncio.create_task(provider_poll(p)) for p in providers_cfg["providers"]]

    try:
        await asyncio.gather(*tasks)
    finally:
        await db.close()


@app.command()
def run(providers_file: str = None):
    """Run incremental polling for all providers."""
    pf = providers_file or PROVIDERS_FILE
    with open(pf, "r") as fh:
        providers_cfg = yaml.safe_load(fh)
    asyncio.run(_run_loop(providers_cfg))


# ----------------------------------------------------------
# BACKFILL COMMAND (MULTI-PAIR, MULTI-DAY)
# ----------------------------------------------------------
@app.command()
def backfill(provider_name: str, years: int = 5, providers_file: str = None):
    """
    Download historical data for the given provider for last N years.
    """
    pf = providers_file or PROVIDERS_FILE
    with open(pf, "r") as fh:
        providers_cfg = yaml.safe_load(fh)

    provider = next((p for p in providers_cfg["providers"] if p["name"] == provider_name), None)
    if not provider:
        raise RuntimeError(f"Provider '{provider_name}' not found in providers.yaml")

    start = datetime.utcnow() - timedelta(days=years * 365)
    end = datetime.utcnow()

    asyncio.run(_do_backfill(provider, start, end))


async def _do_backfill(provider, start, end):
    print(f"\n🔄 Backfilling {provider['name']} from {start.date()} → {end.date()}\n")

    db = DownloadDB(DB_PATH)
    await db.init()
    s3 = S3Client(S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    dl = ProviderDownloader(provider, s3, db)

    await dl.backfill_range(start=start, end=end)
    await db.close()

    print("\n✅ Backfill complete.\n")
