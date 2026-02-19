from __future__ import annotations

import datetime as dt
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
    """Minimal Docker wrapper focused on read-only introspection."""

    def __init__(self) -> None:
        # Uses DOCKER_HOST or /var/run/docker.sock by default.
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
