"""
Standalone async downloader for testing HTTP connections and file writes.

Usage:
    python test_downloader_async.py --url https://httpbin.org/html --out ./download_test.html
"""

import argparse
import asyncio
from pathlib import Path

import aiofiles
import aiohttp

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Connection": "keep-alive",
}


async def fetch_file(url: str, out_path: str, disable_ssl: bool = False):
    connector = aiohttp.TCPConnector(ssl=False) if disable_ssl else aiohttp.TCPConnector()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"→ Fetching: {url}")
        async with session.request(
            "GET", url, headers=HEADERS, timeout=60, params={}, auth=None
        ) as resp:
            resp.raise_for_status()
            content = await resp.content.read()
            print(f"✓ Status: {resp.status}, received {len(content)} bytes")

            async with aiofiles.open(out_path, "wb") as f:
                await f.write(content)
            print(f"✓ Saved to: {out_path}")

            # Show preview (if text)
            ct = resp.headers.get("Content-Type", "")
            if "text" in ct or "html" in ct:
                snippet = content.decode(errors="ignore")[:300]
                print("\nPreview (first 300 chars):\n", "-" * 50)
                print(snippet)
                print("-" * 50)
            else:
                print(f"Content-Type: {ct}")


def main():
    parser = argparse.ArgumentParser(description="Simple async downloader test")
    parser.add_argument("--url", required=True, help="URL to download")
    parser.add_argument("--out", default="./downloaded_file", help="Output file path")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL verification")
    args = parser.parse_args()

    asyncio.run(fetch_file(args.url, args.out, disable_ssl=args.no_ssl))


if __name__ == "__main__":
    main()
