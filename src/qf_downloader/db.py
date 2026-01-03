import aiosqlite
import asyncio
from pathlib import Path
import datetime


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    url TEXT NOT NULL,
    checksum TEXT,
    s3_key TEXT,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_FETCH_TABLE = """
CREATE TABLE IF NOT EXISTS fetch_status (
    provider TEXT PRIMARY KEY,
    last_successful TIMESTAMP
)
"""

class DownloadDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.execute(CREATE_TABLE_SQL)
        await self._conn.execute(CREATE_FETCH_TABLE)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def exists_checksum(self, provider: str, checksum: str) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM downloads WHERE provider = ? AND checksum = ? LIMIT 1", (provider, checksum)
        ) as cur:
            row = await cur.fetchone()
            return row is not None

    async def add_download(self, provider: str, url: str, checksum: str, s3_key: str):
        await self._conn.execute(
            "INSERT INTO downloads (provider, url, checksum, s3_key) VALUES (?, ?, ?, ?)",
            (provider, url, checksum, s3_key)
        )
        # Update or insert the last_successful timestamp
        now = datetime.datetime.utcnow()
        await self._conn.execute(
            """
            INSERT INTO fetch_status (provider, last_successful)
            VALUES (?, ?)
            ON CONFLICT(provider) DO UPDATE SET last_successful = excluded.last_successful
            """,
            (provider, now),
        )
        await self._conn.commit()


    async def get_last_successful(self, provider):
        """Return the last successful fetch timestamp (UTC) or None."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                    "SELECT last_successful FROM fetch_status WHERE provider = ?",
                    (provider,),
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    return datetime.datetime.fromisoformat(row[0])
                return None


# Backwards-compatible synchronous DB wrapper used by integration tests
import sqlite3


class Database:
    """Simple synchronous sqlite-backed helper used by integration tests."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)

    def create_tables(self):
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self._conn.commit()

    def insert_download(self, name: str, status: str):
        cur = self._conn.cursor()
        cur.execute("INSERT INTO downloads (name, status) VALUES (?, ?)", (name, status))
        self._conn.commit()

    def get_downloads(self):
        cur = self._conn.cursor()
        cur.execute("SELECT id, name, status, created_at FROM downloads ORDER BY id")
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({"id": r[0], "name": r[1], "status": r[2], "created_at": r[3]})
        return result