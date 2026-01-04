import asyncio

from qf_downloader.db import DownloadDB


def test_download_db_add_and_exists_checksum(tmp_path) -> None:
    db_path = tmp_path / "downloads.db"
    db = DownloadDB(str(db_path))

    async def scenario() -> None:
        await db.init()

        provider_key = "provider_pair"
        checksum = "abc123"

        assert await db.exists_checksum(provider_key, checksum) is False
        assert await db.get_last_successful(provider_key) is None

        await db.add_download(
            provider=provider_key,
            url="https://example.invalid/data.bin",
            checksum=checksum,
            s3_key="provider/pair/20240101/file.bin",
        )

        assert await db.exists_checksum(provider_key, checksum) is True
        assert await db.get_last_successful(provider_key) is not None

        await db.close()

    asyncio.run(scenario())
