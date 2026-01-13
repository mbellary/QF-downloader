import asyncio
from datetime import datetime, timedelta

import click
import typer

from .config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    DB_PATH,
    MACRO_PROVIDERS_FILE,
    POLL_INTERVAL_SECONDS,
    PROVIDERS_FILE,
    S3_BUCKET,
)
from .logger import get_logger
from .provider_config import load_providers_config

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
    providers_cfg = load_providers_config(pf)

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
    # Lazy imports keep CLI lightweight for commands like `list-providers`.
    from .db import DownloadDB
    from .downloader import ProviderDownloader
    from .storage import S3Client

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

    providers = [p for p in providers_cfg.get("providers", []) if p.get("enabled", True)]
    tasks = [asyncio.create_task(provider_poll(p)) for p in providers]

    try:
        await asyncio.gather(*tasks)
    finally:
        await db.close()


@app.command()
def run(providers_file: str = None):
    """Run incremental polling for all providers."""
    pf = providers_file or PROVIDERS_FILE
    providers_cfg = load_providers_config(pf)
    asyncio.run(_run_loop(providers_cfg))


# ----------------------------------------------------------
# BACKFILL COMMAND (MULTI-PAIR, MULTI-DAY)
# ----------------------------------------------------------
@app.command()
def backfill(
    provider_name: str | None = typer.Argument(
        None, help="Provider name (positional). Example: backfill dukascopy"
    ),
    provider_name_opt: str | None = typer.Option(
        None, "--provider-name", help="Provider name (option). Example: --provider-name dukascopy"
    ),
    years: int = 5,
    providers_file: str | None = None,
):
    """
    Download historical data for the given provider for last N years.
    """
    provider_name_effective = provider_name_opt or provider_name
    if not provider_name_effective:
        raise typer.BadParameter("Missing provider name (use PROVIDER_NAME or --provider-name)")

    pf = providers_file or PROVIDERS_FILE
    providers_cfg = load_providers_config(pf)

    provider = next(
        (p for p in providers_cfg["providers"] if p["name"] == provider_name_effective), None
    )
    if not provider:
        raise RuntimeError(f"Provider '{provider_name_effective}' not found in providers config")

    start = datetime.utcnow() - timedelta(days=years * 365)
    end = datetime.utcnow()

    asyncio.run(_do_backfill(provider, start, end))


@app.command()
def macro_backfill(
    provider_name: str = typer.Argument(..., help="Macro provider name (Phase 0.2)."),
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str | None = typer.Option(
        None, "--end", help="End date (YYYY-MM-DD), defaults to yesterday (UTC)"
    ),
    providers_file: str | None = None,
):
    """Backfill raw macro events (Phase 0.2)."""

    from datetime import UTC, datetime

    from .exogenous_downloader import validate_end_date_not_forward_looking

    start_dt = datetime.fromisoformat(start).replace(tzinfo=UTC)
    end_dt = (
        datetime.fromisoformat(end).replace(tzinfo=UTC)
        if end is not None
        else (datetime.now(UTC) - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    )
    validate_end_date_not_forward_looking(end=end_dt.date(), now=datetime.now(UTC))

    pf = providers_file or str(MACRO_PROVIDERS_FILE)
    providers_cfg = load_providers_config(pf)
    provider = next(
        (
            p
            for p in providers_cfg.get("providers", [])
            if p.get("name") == provider_name
            and str(p.get("artifact_type", "")).lower() == "macro_events"
        ),
        None,
    )
    if not provider:
        raise RuntimeError(f"Macro provider '{provider_name}' not found in {pf}")

    if not bool(provider.get("enabled", True)):
        raise RuntimeError(f"Macro provider '{provider_name}' is disabled (enabled=false) in {pf}")

    from pathlib import Path

    from .quant_allowlist import is_allowlisted_macro_event_provider

    repo_root = Path(__file__).resolve().parents[2]
    if not is_allowlisted_macro_event_provider(provider_name=provider_name, repo_root=repo_root):
        raise RuntimeError(
            f"Macro provider '{provider_name}' is not allowlisted by Quant Q0.7; "
            "choose an approved provider or set enabled=false"
        )

    asyncio.run(_do_exogenous_backfill(provider, start_dt, end_dt))


@app.command()
def news_backfill(
    provider_name: str = typer.Argument(..., help="News provider name (Phase 0.2)."),
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str | None = typer.Option(
        None, "--end", help="End date (YYYY-MM-DD), defaults to yesterday (UTC)"
    ),
    providers_file: str | None = None,
):
    """Backfill raw news (Phase 0.2)."""

    from datetime import UTC, datetime

    from .exogenous_downloader import validate_end_date_not_forward_looking

    start_dt = datetime.fromisoformat(start).replace(tzinfo=UTC)
    end_dt = (
        datetime.fromisoformat(end).replace(tzinfo=UTC)
        if end is not None
        else (datetime.now(UTC) - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    )
    validate_end_date_not_forward_looking(end=end_dt.date(), now=datetime.now(UTC))

    pf = providers_file or str(MACRO_PROVIDERS_FILE)
    providers_cfg = load_providers_config(pf)
    provider = next(
        (
            p
            for p in providers_cfg.get("providers", [])
            if p.get("name") == provider_name and str(p.get("artifact_type", "")).lower() == "news"
        ),
        None,
    )
    if not provider:
        raise RuntimeError(f"News provider '{provider_name}' not found in {pf}")

    if not bool(provider.get("enabled", True)):
        raise RuntimeError(f"News provider '{provider_name}' is disabled (enabled=false) in {pf}")

    asyncio.run(_do_exogenous_backfill(provider, start_dt, end_dt))


async def _do_backfill(provider, start, end):
    print(f"\n🔄 Backfilling {provider['name']} from {start.date()} → {end.date()}\n")

    # Lazy imports keep CLI lightweight for commands like `list-providers`.
    from .db import DownloadDB
    from .downloader import ProviderDownloader
    from .storage import S3Client

    db = DownloadDB(DB_PATH)
    await db.init()
    s3 = S3Client(S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    dl = ProviderDownloader(provider, s3, db)

    await dl.backfill_range(start=start, end=end)
    await db.close()

    print("\n✅ Backfill complete.\n")


async def _do_exogenous_backfill(provider, start, end):
    print(f"\n🔄 Backfilling {provider['name']} (Phase 0.2) from {start.date()} → {end.date()}\n")

    from .db import DownloadDB
    from .exogenous_downloader import ExogenousProviderDownloader
    from .storage import S3Client

    db = DownloadDB(DB_PATH)
    await db.init()
    s3 = S3Client(S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
    dl = ExogenousProviderDownloader(provider=provider, s3=s3, db=db)

    await dl.backfill_range(start=start, end=end)
    await db.close()

    print("\n✅ Phase 0.2 backfill complete.\n")


def main() -> None:
    """Module entrypoint for `python -m qf_downloader.cli`."""

    app()


if __name__ == "__main__":
    main()
