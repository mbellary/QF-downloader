import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def load_quant_return_spec(repo_root: Path) -> dict[str, Any]:
    """Load Quant Q0.1 return/session contract.

    Note: `docs/quant/return_calculation.yaml` currently contains JSON.
    YAML 1.2 is a superset of JSON; however, we intentionally parse via json
    to keep the behavior explicit and deterministic.
    """

    spec_path = repo_root / "docs" / "quant" / "return_calculation.yaml"
    raw = spec_path.read_text(encoding="utf-8")
    return json.loads(raw)


def quant_spec_sha256(repo_root: Path) -> str:
    spec_path = repo_root / "docs" / "quant" / "return_calculation.yaml"
    return sha256_file(spec_path)


def build_sidecar_metadata(
    *,
    repo_root: Path,
    provider: str,
    artifact_type: str | None,
    pair: str,
    date: str,
    url: str,
    http_method: str,
    request_headers: dict[str, str],
    raw_sha256: str,
    s3_bucket: str | None,
    s3_key: str | None,
    local_path: str | None,
) -> dict[str, Any]:
    spec = load_quant_return_spec(repo_root)

    def _redact(headers: dict[str, str]) -> dict[str, str]:
        redacted: dict[str, str] = {}
        for key, value in headers.items():
            lk = key.lower()
            if "authorization" in lk or "api-key" in lk or lk.endswith("key"):
                redacted[key] = "REDACTED"
            else:
                redacted[key] = value
        return redacted

    metadata: dict[str, Any] = {
        "schema_id": "infra.phase0.raw_market_ingestion",
        "schema_version": "1.0.0",
        "provider": provider,
        "artifact_type": artifact_type,
        "pair": pair,
        "date": date,
        "source": {
            "url": url,
            "http_method": http_method,
            "request_headers_redacted": _redact(request_headers),
        },
        "hashes": {"sha256": raw_sha256},
        "time_contract": {
            "timezone": "UTC",
            "timestamp_unit": "ISO-8601",
            "quant_spec_path": "docs/quant/return_calculation.yaml",
            "quant_spec_sha256": quant_spec_sha256(repo_root),
            "quant_effective_date": spec.get("effective_date"),
        },
        "storage": {
            "local_path": local_path,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        },
        "ingested_at_utc": datetime.now(UTC).isoformat(),
    }

    return metadata


def build_macro_news_sidecar_metadata(
    *,
    repo_root: Path,
    provider: str,
    artifact_type: str,
    partition_date_utc: str,
    url: str,
    http_method: str,
    request_headers: dict[str, str],
    raw_sha256: str,
    s3_bucket: str | None,
    s3_key: str | None,
    local_path: str | None,
) -> dict[str, Any]:
    spec = load_quant_return_spec(repo_root)

    def _redact(headers: dict[str, str]) -> dict[str, str]:
        redacted: dict[str, str] = {}
        for key, value in headers.items():
            lk = key.lower()
            if "authorization" in lk or "api-key" in lk or lk.endswith("key"):
                redacted[key] = "REDACTED"
            else:
                redacted[key] = value
        return redacted

    return {
        "schema_id": "infra.phase0.macro_news_ingestion",
        "schema_version": "1.0.0",
        "provider": provider,
        "artifact_type": artifact_type,
        "partition_date_utc": partition_date_utc,
        "source": {
            "url": url,
            "http_method": http_method,
            "request_headers_redacted": _redact(request_headers),
        },
        "hashes": {"sha256": raw_sha256},
        "quant_contracts": {
            "timezone": "UTC",
            "q0_1_return_calculation_sha256": quant_spec_sha256(repo_root),
            "q0_1_effective_date": spec.get("effective_date"),
            "q0_1_return_calculation_path": "docs/quant/return_calculation.yaml",
        },
        "storage": {
            "local_path": local_path,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        },
        "ingested_at_utc": datetime.now(UTC).isoformat(),
    }


def update_rollup_manifest(repo_root: Path, entry: dict[str, Any]) -> None:
    """Upsert a partition entry into pipelines/ingestion/fx/metadata.json.

    This is deterministic and idempotent for single-process ingestion.
    """

    manifest_path = repo_root / "pipelines" / "ingestion" / "fx" / "metadata.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def _key(e: dict[str, Any]) -> tuple[str, str, str, str]:
        return (
            str(e.get("provider")),
            str(e.get("artifact_type")),
            str(e.get("pair")),
            str(e.get("date")),
        )

    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        current = {"schema_version": "1.0.0", "generated_at_utc": None, "entries": []}

    entries: list[dict[str, Any]] = list(current.get("entries", []))
    entries_by_key = {_key(e): e for e in entries}
    entries_by_key[_key(entry)] = entry

    updated_entries = [entries_by_key[k] for k in sorted(entries_by_key.keys())]

    current["generated_at_utc"] = datetime.now(UTC).isoformat()
    current["entries"] = updated_entries

    manifest_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_rollup_manifest_macro_news(repo_root: Path, entry: dict[str, Any]) -> None:
    """Upsert a partition entry into pipelines/ingestion/macro_news/metadata.json."""

    manifest_path = repo_root / "pipelines" / "ingestion" / "macro_news" / "metadata.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def _key(e: dict[str, Any]) -> tuple[str, str, str]:
        return (
            str(e.get("provider")),
            str(e.get("artifact_type")),
            str(e.get("partition_date_utc") or e.get("date")),
        )

    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        current = {"schema_version": "1.0.0", "generated_at_utc": None, "entries": []}

    entries: list[dict[str, Any]] = list(current.get("entries", []))
    entries_by_key = {_key(e): e for e in entries}
    entries_by_key[_key(entry)] = entry

    updated_entries = [entries_by_key[k] for k in sorted(entries_by_key.keys())]

    current["generated_at_utc"] = datetime.now(UTC).isoformat()
    current["entries"] = updated_entries

    manifest_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
