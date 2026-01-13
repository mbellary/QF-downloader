import asyncio
import json
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from qf_downloader.metadata import quant_spec_sha256

exogenous = pytest.importorskip(
    "qf_downloader.exogenous_downloader",
    reason="Phase 0.2 exogenous downloader not implemented yet",
)

ExogenousProviderDownloader = exogenous.ExogenousProviderDownloader
validate_end_date_not_forward_looking = exogenous.validate_end_date_not_forward_looking


@pytest.mark.parametrize(
    ("artifact_type", "expected_prefix", "expected_filename"),
    [
        (
            "macro_events",
            "data/raw/macro/events/FRED/2024/01/02",
            "macro_events_20240102.json",
        ),
        (
            "news",
            "data/raw/news/fmp/2024/01/02",
            "news_20240102.json",
        ),
    ],
)
def test_p0_2_defaults_to_phase0_deterministic_layout_when_save_path_missing(
    tmp_path, artifact_type: str, expected_prefix: str, expected_filename: str
) -> None:
    provider = {
        "name": "FRED" if artifact_type == "macro_events" else "fmp",
        "artifact_type": artifact_type,
        "url_template": "https://example.invalid/{year}/{month}/{day}.json",
        # Intentionally omit save_path: implementation should use deterministic default.
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=False),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ExogenousProviderDownloader(
        provider=provider,
        s3=s3,
        db=db,
        base_data_dir=str(tmp_path),
    )

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(day=day)

    result = asyncio.run(scenario())

    expected_key = f"{expected_prefix}/{expected_filename}"
    assert result["status"] == "uploaded"
    assert result["key"] == expected_key


def test_p0_2_uploads_sidecar_metadata_with_macro_news_schema_and_utc_binding(tmp_path) -> None:
    provider = {
        "name": "FRED",
        "artifact_type": "macro_events",
        "url_template": "https://example.invalid/{year}/{month}/{day}.json",
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=False),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ExogenousProviderDownloader(
        provider=provider,
        s3=s3,
        db=db,
        base_data_dir=str(tmp_path),
    )

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(day=day)

    result = asyncio.run(scenario())
    assert result["status"] == "uploaded"

    sidecar_calls = [
        call
        for call in s3.upload_file.await_args_list
        if str(call.kwargs.get("key", "")).endswith(".metadata.json")
    ]
    assert len(sidecar_calls) == 1

    sidecar_bytes = sidecar_calls[0].kwargs["content"]
    sidecar = json.loads(sidecar_bytes.decode("utf-8"))

    assert sidecar["schema_id"] == "infra.phase0.macro_news_ingestion"

    # UTC binding + Q0.1 contract hash should be present in one of these shapes.
    import qf_downloader.metadata as metadata_mod

    repo_root = Path(metadata_mod.__file__).resolve().parents[2]
    expected_q0_1_sha = quant_spec_sha256(repo_root=repo_root)

    if "quant_contracts" in sidecar:
        assert sidecar["quant_contracts"]["timezone"] == "UTC"
        assert sidecar["quant_contracts"]["q0_1_return_calculation_sha256"] == expected_q0_1_sha
    else:
        assert sidecar["time_contract"]["timezone"] == "UTC"
        assert sidecar["time_contract"]["quant_spec_sha256"] == expected_q0_1_sha


@pytest.mark.parametrize("exists_already", [False, True])
def test_p0_2_idempotence_upload_or_skip(tmp_path, exists_already: bool) -> None:
    provider = {
        "name": "FRED",
        "artifact_type": "macro_events",
        "url_template": "https://example.invalid/{year}/{month}/{day}.json",
    }

    db = SimpleNamespace(
        exists_checksum=AsyncMock(return_value=exists_already),
        add_download=AsyncMock(),
    )
    s3 = SimpleNamespace(upload_file=AsyncMock())

    dl = ExogenousProviderDownloader(
        provider=provider,
        s3=s3,
        db=db,
        base_data_dir=str(tmp_path),
    )

    content = b"payload"
    dl._fetch = AsyncMock(return_value=(object(), content))

    day = datetime(2024, 1, 2, tzinfo=UTC)

    async def scenario() -> dict:
        return await dl._download_single_day(day=day)

    result = asyncio.run(scenario())

    if exists_already:
        assert result["status"] == "skipped"
        s3.upload_file.assert_not_called()
        db.add_download.assert_not_called()
        return

    assert result["status"] == "uploaded"
    s3.upload_file.assert_awaited()
    db.add_download.assert_awaited_once()


def test_p0_2_rejects_forward_looking_end_date() -> None:
    now = datetime(2024, 1, 3, tzinfo=UTC)
    validate_end_date_not_forward_looking(end=date(2024, 1, 2), now=now)

    with pytest.raises(ValueError, match="forward-looking"):
        validate_end_date_not_forward_looking(end=date(2024, 1, 3), now=now)
