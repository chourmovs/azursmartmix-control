from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class IcecastClient:
    """Read-only Icecast status client (best-effort).

    Default endpoint: /status-json.xsl
    We extract the source matching the configured mount and return:
    - title (if present)
    - artist (if present)
    - listeners, bitrate, server_name, etc. when available
    """

    def __init__(self, scheme: str, host: str, port: int, status_path: str, mount: str) -> None:
        self.scheme = scheme or "http"
        self.host = host
        self.port = int(port)
        self.status_path = status_path or "/status-json.xsl"
        self.mount = mount if mount.startswith("/") else f"/{mount}"
        self.timeout = httpx.Timeout(2.5, connect=1.5)

    def _base(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}"

    async def fetch_status(self) -> Dict[str, Any]:
        url = f"{self._base()}{self.status_path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            # Icecast status-json is usually JSON despite .xsl
            try:
                return r.json()
            except Exception:
                return {"raw_text": r.text}

    @staticmethod
    def _iter_sources(payload: Dict[str, Any]):
        icestats = (payload or {}).get("icestats") or {}
        src = icestats.get("source")
        if src is None:
            return []
        if isinstance(src, list):
            return src
        return [src] if isinstance(src, dict) else []

    async def now_playing(self) -> Dict[str, Any]:
        try:
            payload = await self.fetch_status()
        except Exception as e:
            return {
                "ok": False,
                "source": "icecast",
                "error": str(e),
                "mount": self.mount,
            }

        sources = self._iter_sources(payload)
        match = None
        for s in sources:
            # Icecast uses "listenurl" and/or "mount" depending on version/config
            mount = s.get("mount") or None
            if mount is None:
                listenurl = s.get("listenurl") or ""
                if listenurl.endswith(self.mount):
                    match = s
                    break
            else:
                if str(mount) == self.mount:
                    match = s
                    break

        if match is None:
            return {
                "ok": False,
                "source": "icecast",
                "error": "mount not found in status",
                "mount": self.mount,
                "available": [
                    (s.get("mount") or s.get("listenurl") or "unknown") for s in sources
                ],
            }

        # "title" is what many sources set (often "Artist - Track")
        title = match.get("title") or match.get("yp_currently_playing") or None
        artist = match.get("artist") or None

        return {
            "ok": True,
            "source": "icecast",
            "mount": self.mount,
            "title": title,
            "artist": artist,
            "listeners": match.get("listeners"),
            "listener_peak": match.get("listener_peak"),
            "bitrate": match.get("bitrate"),
            "server_name": match.get("server_name"),
            "genre": match.get("genre"),
            "raw": match,
        }
