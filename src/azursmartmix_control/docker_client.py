from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import docker
from docker.errors import DockerException, NotFound


@dataclass(frozen=True)
class ContainerInfo:
    name: str
    id: str
    image: str
    status: str
    created_at: Optional[str]
    health: Optional[str]
    started_at: Optional[str]


class DockerClient:
    """Minimal Docker wrapper focused on read-only introspection.

    v1 extras:
    - best-effort current track extraction from engine logs.
    """

    # Example line you showed:
    # TIMING ... | AFT#1 ENTER cur=file:///tmp/...wav pos=... dur=...
    _RE_CUR = re.compile(r"\bcur=(?P<cur>\S+)")
    _RE_NEXT = re.compile(r"\bnext=(?P<next>\S+)")
    _RE_POS = re.compile(r"\bpos=(?P<pos>[0-9.]+)s")
    _RE_DUR = re.compile(r"\bdur=(?P<dur>[0-9.]+)")

    def __init__(self) -> None:
        self.client = docker.from_env()

    def ping(self) -> bool:
        try:
            self.client.ping()
            return True
        except DockerException:
            return False

    def get_container_info(self, name: str) -> Optional[ContainerInfo]:
        try:
            c = self.client.containers.get(name)
        except NotFound:
            return None
        except DockerException:
            return None

        attrs = getattr(c, "attrs", {}) or {}
        state = (attrs.get("State") or {})
        health = None
        if isinstance(state.get("Health"), dict):
            health = state["Health"].get("Status")

        created = attrs.get("Created")
        started = state.get("StartedAt")
        image = ""
        try:
            image = (attrs.get("Config") or {}).get("Image") or ""
        except Exception:
            image = ""

        return ContainerInfo(
            name=name,
            id=c.id[:12],
            image=image,
            status=getattr(c, "status", "unknown"),
            created_at=created,
            health=health,
            started_at=started,
        )

    def tail_logs(self, name: str, tail: int = 300) -> str:
        """Return last N lines of container logs (best-effort)."""
        try:
            c = self.client.containers.get(name)
            raw: bytes = c.logs(tail=tail, timestamps=True)  # type: ignore[assignment]
            return raw.decode("utf-8", errors="replace")
        except NotFound:
            return f"[control] container not found: {name}\n"
        except DockerException as e:
            return f"[control] docker error: {e}\n"
        except Exception as e:
            return f"[control] unexpected error: {e}\n"

    def runtime_summary(self, engine_name: str, sched_name: str) -> Dict[str, Any]:
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        return {
            "now_utc": now,
            "docker_ping": self.ping(),
            "engine": self._container_info_dict(engine_name),
            "scheduler": self._container_info_dict(sched_name),
        }

    def _container_info_dict(self, name: str) -> Dict[str, Any]:
        info = self.get_container_info(name)
        if not info:
            return {"name": name, "present": False}
        return {
            "present": True,
            "name": info.name,
            "id": info.id,
            "image": info.image,
            "status": info.status,
            "health": info.health,
            "created_at": info.created_at,
            "started_at": info.started_at,
        }

    def best_effort_now_playing_from_logs(self, engine_container: str, tail: int = 600) -> Dict[str, Any]:
        """Parse engine logs to infer current track (read-only heuristic).

        We look for the last line containing `cur=...` (your TIMING/AFT lines).
        """
        txt = self.tail_logs(engine_container, tail=tail)
        if not txt or txt.startswith("[control]"):
            return {
                "ok": False,
                "source": "engine_logs",
                "engine_container": engine_container,
                "error": txt.strip() if txt else "empty logs",
            }

        last_cur = None
        last_next = None
        last_pos = None
        last_dur = None
        last_line = None

        for line in txt.splitlines():
            m = self._RE_CUR.search(line)
            if m:
                last_cur = m.group("cur")
                last_line = line
                mpos = self._RE_POS.search(line)
                if mpos:
                    last_pos = mpos.group("pos")
                mdur = self._RE_DUR.search(line)
                if mdur:
                    last_dur = mdur.group("dur")

            mn = self._RE_NEXT.search(line)
            if mn:
                last_next = mn.group("next")

        if not last_cur:
            return {
                "ok": False,
                "source": "engine_logs",
                "engine_container": engine_container,
                "error": "no `cur=` pattern found in tail",
            }

        return {
            "ok": True,
            "source": "engine_logs",
            "engine_container": engine_container,
            "current_uri": last_cur,
            "position_s": float(last_pos) if last_pos is not None else None,
            "duration_s": float(last_dur) if last_dur is not None else None,
            "last_next_uri_seen": last_next,
            "evidence": last_line,
        }
