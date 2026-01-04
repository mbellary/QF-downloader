import hashlib
import mimetypes
from pathlib import Path

import aiofiles


async def file_checksum(path: str, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    async with aiofiles.open(path, "rb") as f:
        while True:
            chunk = await f.read(1024 * 64)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def guess_content_type(url: str, filename: str = None):
    if filename:
        ct, _ = mimetypes.guess_type(filename)
        if ct:
            return ct
    # fallback via extension
    if url.endswith(".csv"):
        return "text/csv"
    if url.endswith(".pdf"):
        return "application/pdf"
    if url.endswith(".html") or url.endswith(".htm"):
        return "text/html"
    return "application/octet-stream"
