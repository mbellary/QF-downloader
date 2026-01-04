import asyncio
import hashlib

from qf_downloader.utils import ensure_dir, file_checksum, guess_content_type


def test_ensure_dir_idempotent(tmp_path) -> None:
    target = tmp_path / "a" / "b" / "c"

    ensure_dir(target)
    assert target.exists()

    ensure_dir(target)
    assert target.exists()


def test_guess_content_type_prefers_filename() -> None:
    assert (
        guess_content_type(url="https://example.invalid/anything", filename="file.csv")
        == "text/csv"
    )
    assert (
        guess_content_type(url="https://example.invalid/anything", filename="file.pdf")
        == "application/pdf"
    )
    assert (
        guess_content_type(url="https://example.invalid/anything", filename="file.html")
        == "text/html"
    )


def test_guess_content_type_falls_back_to_url_extension() -> None:
    assert guess_content_type(url="https://example.invalid/x.csv") == "text/csv"
    assert guess_content_type(url="https://example.invalid/x.pdf") == "application/pdf"
    assert guess_content_type(url="https://example.invalid/x.html") == "text/html"
    assert guess_content_type(url="https://example.invalid/x.unknown") == "application/octet-stream"


def test_file_checksum_sha256(tmp_path) -> None:
    payload = b"hello world\n"
    p = tmp_path / "hello.txt"
    p.write_bytes(payload)

    actual = asyncio.run(file_checksum(str(p), algo="sha256"))
    expected = hashlib.sha256(payload).hexdigest()

    assert actual == expected
