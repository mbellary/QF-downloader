from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def load_providers_config(path: str | Path) -> Dict[str, Any]:
    """Load provider configuration from JSON (preferred) or YAML (legacy).

    The runtime expects a dict with a top-level ``providers`` list.
    """

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Providers config file not found: {p}")

    raw: Dict[str, Any]
    if p.suffix.lower() in {".json"}:
        raw = json.loads(p.read_text(encoding="utf-8"))
    elif p.suffix.lower() in {".yaml", ".yml"}:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    else:
        # Be permissive: try JSON first, then YAML.
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            raw = yaml.safe_load(p.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError(f"Providers config must be a mapping, got: {type(raw).__name__}")

    providers = raw.get("providers")
    if providers is None:
        raise ValueError("Providers config missing required top-level key: 'providers'")
    if not isinstance(providers, list):
        raise ValueError("Providers config key 'providers' must be a list")

    normalized = {**raw}
    normalized["providers"] = [_normalize_provider(p) for p in providers]
    return normalized


def _normalize_provider(provider: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(provider, dict):
        raise ValueError("Each provider entry must be a mapping")

    p: Dict[str, Any] = {**provider}

    # Legacy: providers_single_pair.yaml uses 'url'
    if "url_template" not in p and "url" in p:
        p["url_template"] = p.pop("url")

    # Normalize enabled
    if "enabled" not in p:
        p["enabled"] = True

    # Normalize params
    params = p.get("params") or {}
    if isinstance(params, dict):
        params = {**params}

        # Legacy key spelling
        if "apikey_env" in params and "api_key_env" not in params:
            params["api_key_env"] = params.pop("apikey_env")

        # providers_single_pair.yaml had access_key set to the ENV var name.
        # Convert to *_env form so auth can resolve it.
        if "access_key" in params and "access_key_env" not in params:
            v = params.get("access_key")
            if isinstance(v, str) and v.isupper() and " " not in v:
                params.pop("access_key")
                params["access_key_env"] = v

        p["params"] = params

    # Normalize auth
    auth = p.get("auth") or {}
    if not isinstance(auth, dict):
        auth = {}

    # Some configs rely on query api key auth but only specify params.*_env.
    if auth.get("type") == "query_api_key":
        if "api_key_env" not in auth:
            if isinstance(params, dict):
                if "api_key_env" in params:
                    auth["api_key_env"] = params["api_key_env"]
                elif "access_key_env" in params:
                    auth["api_key_env"] = params["access_key_env"]

    p["auth"] = auth

    # Normalize artifact_type
    if "artifact_type" not in p:
        t = p.get("type")
        if isinstance(t, str) and t.lower() not in {"api"}:
            p["artifact_type"] = t
        else:
            # Heuristic fallback
            name = str(p.get("name", "")).lower()
            save_path = str(p.get("save_path", "")).lower()
            if "macro" in save_path or name.startswith("econ_"):
                p["artifact_type"] = "macro"
            elif "tick" in name:
                p["artifact_type"] = "tick"
            else:
                p["artifact_type"] = "ohlcv"

    # Normalize supports_pairs
    supports_pairs = p.get("supports_pairs")
    if supports_pairs is None:
        p["supports_pairs"] = ["EURUSD"]

    return p
