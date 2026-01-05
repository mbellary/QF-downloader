import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qf_downloader.downloader import ProviderDownloader
from qf_downloader.utils import guess_content_type


@pytest.mark.parametrize("exists_already", [False, True])
def test_download_single_day_upload_or_skip(tmp_path, exists_already: bool) -> None:
    provider = {
        "name": "testprov",
        "save_path": "testprov/{pair}/{year}/{month}/{day}",
        "url_template": "https://example.invalid/{pair}/{year}/{month}/{day}.bin",
        "artifact_type": "tick",
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=exists_already),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ProviderDownloader(provider=provider, s3=s3, db=db, base_data_dir=str(tmp_path))
    dl.indexer = SimpleNamespace(index_file=AsyncMock())

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(pair="EURUSD", day=day)

    result = asyncio.run(scenario())

    yyyy, mm, dd = "2024", "01", "02"
    filename = f"EURUSD_{yyyy}{mm}{dd}.bin"
    expected_s3_key = f"testprov/EURUSD/{yyyy}/{mm}/{dd}/{filename}"
    expected_url = f"https://example.invalid/EURUSD/{yyyy}/{mm}/{dd}.bin"

    if exists_already:
        assert result["status"] == "skipped"
        s3.upload_file.assert_not_called()
        db.add_download.assert_not_called()
        dl.indexer.index_file.assert_not_called()
        return

    assert result["status"] == "uploaded"
    assert result["pair"] == "EURUSD"
    assert result["key"] == expected_s3_key

    expected_content_type = guess_content_type(expected_url, filename)

    expected_sidecar_key = f"{expected_s3_key}.metadata.json"

    keys = [call.kwargs["key"] for call in s3.upload_file.await_args_list]
    assert expected_s3_key in keys
    assert expected_sidecar_key in keys

    raw_call = next(
        call for call in s3.upload_file.await_args_list if call.kwargs["key"] == expected_s3_key
    )
    assert raw_call.kwargs["content"] == content
    assert raw_call.kwargs["content_type"] == expected_content_type
    db.add_download.assert_awaited_once()
    dl.indexer.index_file.assert_awaited_once_with(
        provider="testprov",
        pair="EURUSD",
        date=f"{yyyy}{mm}{dd}",
        s3_key=expected_s3_key,
        artifact_type="tick",
    )


def test_prepare_headers_injects_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret")

    provider = {
        "name": "prov",
        "save_path": "x/{pair}/{year}/{month}/{day}",
        "url_template": "https://example.invalid/{pair}/{year}/{month}/{day}.bin",
        "auth": {"type": "header_api_key", "header_env": "TEST_API_KEY", "header_name": "X-API"},
    }

    dl = ProviderDownloader(provider=provider, s3=SimpleNamespace(), db=SimpleNamespace())
    headers = dl._prepare_headers()

    assert headers["X-API"] == "secret"


def test_prepare_auth_basic(monkeypatch) -> None:
    monkeypatch.setenv("TEST_USER", "u")
    monkeypatch.setenv("TEST_PASS", "p")

    provider = {
        "name": "prov",
        "save_path": "x/{pair}/{year}/{month}/{day}",
        "url_template": "https://example.invalid/{pair}/{year}/{month}/{day}.bin",
        "auth": {"type": "basic", "user_env": "TEST_USER", "pass_env": "TEST_PASS"},
    }

    dl = ProviderDownloader(provider=provider, s3=SimpleNamespace(), db=SimpleNamespace())
    auth = dl._prepare_auth()

    assert auth is not None
    assert getattr(auth, "login", None) == "u"
