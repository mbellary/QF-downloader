import json
from pathlib import Path


def _normalize_provider_name(name: str) -> str:
    return "".join(ch.lower() for ch in name.strip() if ch.isalnum())


def load_q0_7_macro_event_allowlist(repo_root: Path) -> set[str]:
    """Load Quant Q0.7 macro event approved providers.

    Note: `docs/quant/data_providers/macro_event_providers.yaml` currently contains JSON.
    """

    allowlist_path = repo_root / "docs" / "quant" / "data_providers" / "macro_event_providers.yaml"
    payload = json.loads(allowlist_path.read_text(encoding="utf-8"))
    approved = payload.get("approved_providers", [])
    return {_normalize_provider_name(p.get("name", "")) for p in approved if p.get("name")}


def is_allowlisted_macro_event_provider(*, provider_name: str, repo_root: Path) -> bool:
    allowlist = load_q0_7_macro_event_allowlist(repo_root)
    return _normalize_provider_name(provider_name) in allowlist
