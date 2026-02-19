from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


def _as_kv(item: Any) -> Optional[Tuple[str, str]]:
    """Convert docker-compose environment entries to (key, value).

    Supports:
    - ["A=1", "B=2"]
    - {"A": "1", "B": 2}
    - ["A"] (means inherited/empty -> we keep empty string)
    """
    if isinstance(item, str):
        if "=" in item:
            k, v = item.split("=", 1)
            return k.strip(), v
        return item.strip(), ""
    return None


def read_compose_services_env(compose_path: str) -> Dict[str, Any]:
    """Read compose and return service->env mapping (raw, best-effort)."""
    if not compose_path or not os.path.exists(compose_path):
        return {
            "present": False,
            "path": compose_path,
            "error": "compose file not found",
            "services": {},
        }

    try:
        with open(compose_path, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        return {
            "present": True,
            "path": compose_path,
            "error": f"failed to read/parse yaml: {e}",
            "services": {},
        }

    services = (doc or {}).get("services") or {}
    out: Dict[str, Any] = {}

    for svc_name, svc in services.items():
        env = (svc or {}).get("environment", None)
        env_out: Dict[str, str] = {}

        if isinstance(env, dict):
            for k, v in env.items():
                env_out[str(k)] = "" if v is None else str(v)
        elif isinstance(env, list):
            for it in env:
                kv = _as_kv(it)
                if kv:
                    k, v = kv
                    env_out[k] = v
        elif env is None:
            env_out = {}
        else:
            # weird type
            env_out = {"__error__": f"unsupported environment type: {type(env)}"}

        out[str(svc_name)] = {"environment": env_out}

    return {
        "present": True,
        "path": compose_path,
        "error": None,
        "services": out,
    }


def get_service_env(compose_path: str, service: str) -> Dict[str, Any]:
    """Return env vars of a specific service."""
    data = read_compose_services_env(compose_path)
    if not data.get("present"):
        return data

    services = data.get("services") or {}
    if service not in services:
        return {
            "present": True,
            "path": compose_path,
            "error": None,
            "service": service,
            "found": False,
            "environment": {},
            "available_services": sorted(list(services.keys())),
        }

    env = (services[service] or {}).get("environment") or {}
    return {
        "present": True,
        "path": compose_path,
        "error": None,
        "service": service,
        "found": True,
        "environment": env,
        "available_services": sorted(list(services.keys())),
    }
