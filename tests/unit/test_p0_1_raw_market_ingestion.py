import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qf_downloader.downloader import ProviderDownloader


def test_download_supports_base_quote_placeholders(tmp_path) -> None:
    """Phase 0.1 requires URL templates to support {base}/{quote} as well as {pair}."""

    provider = {
        "name": "testprov",
        "url_template": "https://example.invalid/{base}{quote}/{year}/{month}/{day}.bin",
        "save_path": "raw/testprov/{pair}/{year}/{month}/{day}",
        "supports_pairs": ["EURUSD"],
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=False),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))
    dl.indexer = SimpleNamespace(index_file=AsyncMock())
    dl.indexer = SimpleNamespace(index_file=AsyncMock())

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(pair="EURUSD", day=day)

    result = asyncio.run(scenario())

    assert result["status"] == "uploaded"


def test_download_defaults_to_phase0_deterministic_layout_when_save_path_missing(tmp_path) -> None:
    """Phase 0.1 design: save path derives from artifact_type/provider/pair/date."""

    provider = {
        "name": "dukascopy",
        "artifact_type": "tick",
        "url_template": "https://example.invalid/{pair}/{year}/{month}/{day}.bin",
        "supports_pairs": ["EURUSD"],
        # Intentionally omit save_path: implementation should use deterministic default.
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=False),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))
    dl.indexer = SimpleNamespace(index_file=AsyncMock())
    dl.indexer = SimpleNamespace(index_file=AsyncMock())

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(pair="EURUSD", day=day)

    result = asyncio.run(scenario())

    yyyy, mm, dd = "2024", "01", "02"
    filename = f"EURUSD_{yyyy}{mm}{dd}.bin"
    expected_prefix = f"data/raw/fx/tick/dukascopy/EURUSD/{yyyy}/{mm}/{dd}"
    expected_s3_key = f"{expected_prefix}/{filename}"

    assert result["key"] == expected_s3_key


def test_download_uploads_sidecar_metadata_json(tmp_path) -> None:
    """Phase 0.1 design: upload raw artifact + sidecar metadata JSON deterministically."""

    provider = {
        "name": "dukascopy",
        "artifact_type": "tick",
        "url_template": "https://example.invalid/{pair}/{year}/{month}/{day}.bin",
        "supports_pairs": ["EURUSD"],
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=False),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))
    dl.indexer = SimpleNamespace(index_file=AsyncMock())
    dl.indexer = SimpleNamespace(index_file=AsyncMock())

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(pair="EURUSD", day=day)

    result = asyncio.run(scenario())

    yyyy, mm, dd = "2024", "01", "02"
    filename = f"EURUSD_{yyyy}{mm}{dd}.bin"
    expected_prefix = f"data/raw/fx/tick/dukascopy/EURUSD/{yyyy}/{mm}/{dd}"
    raw_key = f"{expected_prefix}/{filename}"
    sidecar_key = f"{raw_key}.metadata.json"

    assert result["key"] == raw_key

    keys = [call.kwargs["key"] for call in s3.upload_file.await_args_list]
    assert raw_key in keys
    assert sidecar_key in keys


@pytest.mark.parametrize(
    ("pair", "base", "quote"),
    [
        ("EURUSD", "EUR", "USD"),
        ("USDJPY", "USD", "JPY"),
    ],
)
def test_pair_is_split_into_base_and_quote(pair: str, base: str, quote: str, tmp_path) -> None:
    """Phase 0.1 URL template formatting requires base/quote derivation from pair."""

    provider = {
        "name": "testprov",
        "url_template": "https://example.invalid/{base}/{quote}/{year}{month}{day}.bin",
        "save_path": "raw/testprov/{pair}/{year}/{month}/{day}",
        "supports_pairs": [pair],
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=False),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))
    dl.indexer = SimpleNamespace(index_file=AsyncMock())
    dl.indexer = SimpleNamespace(index_file=AsyncMock())

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(pair=pair, day=day)

    asyncio.run(scenario())

    # Assert that the URL formatting used base/quote correctly.
    called_url = dl._fetch.await_args.args[2]
    assert f"/{base}/{quote}/" in called_url
