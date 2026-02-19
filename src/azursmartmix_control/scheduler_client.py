from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class SchedulerClient:
    """Proxy client to AzurSmartMix scheduler API.

    v1 assumptions:
    - scheduler exposes /health
    - scheduler exposes /next1 (and optionally /next?n=10 or /next10 etc.)
    Since implementations vary, we do tolerant probing.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(2.5, connect=1.5)

    async def health(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(f"{self.base_url}/health")
            r.raise_for_status()
            data = self._safe_json(r)
            return data if isinstance(data, dict) else {"ok": True, "raw": data}

    async def now_playing(self) -> Dict[str, Any]:
        """Best-effort now playing.
        If scheduler doesn't expose it, we return an 'unknown' structure.
        """
        candidates = [
            "/now", "/now_playing", "/playing", "/current",
            "/np", "/status",
        ]
        for path in candidates:
            data = await self._try_get_json(path)
            if data is not None:
                return {"source": path, "data": data}

        return {
            "source": None,
            "data": {
                "note": "Scheduler does not expose a now-playing endpoint (v1 fallback).",
            },
        }

    async def upcoming(self, n: int = 10) -> Dict[str, Any]:
        """Best-effort upcoming queue."""
        data = await self._try_get_json(f"/next?n={n}")
        if data is not None:
            return {"source": f"/next?n={n}", "data": data}

        data = await self._try_get_json(f"/next{n}")
        if data is not None:
            return {"source": f"/next{n}", "data": data}

        data = await self._try_get_json("/next1")
        if data is not None:
            return {"source": "/next1", "data": data}

        return {
            "source": None,
            "data": {"note": "No upcoming endpoint found on scheduler."},
        }

    async def _try_get_json(self, path: str) -> Optional[Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                r = await client.get(f"{self.base_url}{path}")
                if r.status_code >= 400:
                    return None
                return self._safe_json(r)
            except Exception:
                return None

    @staticmethod
    def _safe_json(r: httpx.Response) -> Any:
        ct = (r.headers.get("content-type") or "").lower()
        if "application/json" in ct:
            try:
                return r.json()
            except Exception:
                return {"raw_text": r.text}
        txt = r.text.strip()
        return {"raw_text": txt} if txt else {}
