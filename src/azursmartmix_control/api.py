from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from azursmartmix_control.config import Settings
from azursmartmix_control.docker_client import DockerClient
from azursmartmix_control.scheduler_client import SchedulerClient
from azursmartmix_control.compose_reader import get_service_env
from azursmartmix_control.icecast_client import IcecastClient


def _fmt_duration(seconds: Optional[int]) -> Optional[str]:
    if seconds is None:
        return None
    s = int(seconds)
    if s < 0:
        s = 0
    d, rem = divmod(s, 86400)
    h, rem = divmod(rem, 3600)
    m, sec = divmod(rem, 60)
    if d > 0:
        return f"{d}d {h:02d}:{m:02d}:{sec:02d}"
    return f"{h:02d}:{m:02d}:{sec:02d}"


def create_api(settings: Settings) -> FastAPI:
    app = FastAPI(title="AzurSmartMix Control API", version="0.1.0")

    docker_client = DockerClient()

    now_ep = os.getenv("SCHED_NOW_ENDPOINT", "").strip() or None
    sched = SchedulerClient(settings.sched_base_url, now_endpoint=now_ep)

    ice = IcecastClient(
        scheme=settings.icecast_scheme,
        host=settings.icecast_host,
        port=settings.icecast_port,
        status_path=settings.icecast_status_path,
        mount=settings.icecast_mount,
    )

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"ok": True}

    @app.get("/status")
    def status() -> Dict[str, Any]:
        return docker_client.runtime_summary(settings.engine_container, settings.scheduler_container)

    @app.get("/logs", response_class=PlainTextResponse)
    def logs(
        service: str = Query(..., description="engine|scheduler|<container_name>"),
        tail: int = Query(0, description="lines to tail (0 = default)"),
    ) -> str:
        tail_eff = tail if tail > 0 else settings.log_tail_lines_default
        tail_eff = max(1, min(tail_eff, settings.log_tail_lines_max))

        if service == "engine":
            name = settings.engine_container
        elif service == "scheduler":
            name = settings.scheduler_container
        else:
            name = service

        return docker_client.tail_logs(name=name, tail=tail_eff)

    # --- scheduler proxy (still useful for /next) ---
    @app.get("/scheduler/upcoming")
    async def scheduler_upcoming(n: int = Query(10, ge=1, le=50)) -> JSONResponse:
        data = await sched.upcoming(n=n)
        return JSONResponse(data)

    # --- compose env (your "config") ---
    @app.get("/panel/engine_env")
    def panel_engine_env() -> Dict[str, Any]:
        return get_service_env(settings.compose_path, settings.compose_service_engine)

    # --- panel runtime ---
    @app.get("/panel/runtime")
    def panel_runtime() -> Dict[str, Any]:
        raw = docker_client.runtime_summary(settings.engine_container, settings.scheduler_container)

        eng = raw.get("engine") or {}
        sch = raw.get("scheduler") or {}

        def pack(x: Dict[str, Any]) -> Dict[str, Any]:
            if not x.get("present"):
                return {"present": False, "name": x.get("name"), "status": "missing"}
            return {
                "present": True,
                "name": x.get("name"),
                "image": x.get("image"),
                "status": x.get("status"),
                "health": x.get("health"),
                "uptime": _fmt_duration(x.get("uptime_s")),
                "age": _fmt_duration(x.get("age_s")),
            }

        return {
            "now_utc": raw.get("now_utc"),
            "docker_ping": raw.get("docker_ping"),
            "engine": pack(eng),
            "scheduler": pack(sch),
        }

    # --- panel now (Icecast title + infer playlist from scheduler NEXT log) ---
    @app.get("/panel/now")
    async def panel_now() -> Dict[str, Any]:
        ic = await ice.now_playing()
        title = None
        if isinstance(ic, dict) and ic.get("ok"):
            title = ic.get("title") or (ic.get("raw") or {}).get("title")

        # infer playlist from scheduler logs by matching normalized title
        pl = docker_client.infer_playlist_for_title_from_scheduler(
            scheduler_container=settings.scheduler_container,
            current_title=title,
            tail=2500,
        )
        playlist = pl.get("playlist") if isinstance(pl, dict) else None

        # anticipation hint: engine STREAM_START seen recently?
        ss = docker_client.last_engine_stream_start(
            engine_container=settings.engine_container,
            tail=800,
            recent_window_s=10,
        )

        # predicted next: take first upcoming from scheduler NEXT (best user-aligned semantics)
        up = docker_client.compute_upcoming_from_scheduler_next(
            scheduler_container=settings.scheduler_container,
            current_title=title,
            n=5,
            tail=2500,
        )
        predicted_next = None
        if isinstance(up, dict) and up.get("ok"):
            lst = up.get("upcoming") or []
            if isinstance(lst, list) and lst:
                predicted_next = lst[0]

        return {
            "ok": bool(title),
            "title": title,
            "playlist": playlist,
            "source": "icecast+scheduler_logs",
            "mount": settings.icecast_mount,
            "scheduler_match": pl.get("match") if isinstance(pl, dict) else None,
            "engine_stream_start": ss,
            "predicted_next": predicted_next,
        }

    # --- panel upcoming (from scheduler NEXT log + playlist) ---
    @app.get("/panel/upcoming")
    async def panel_upcoming(n: int = Query(10, ge=1, le=30)) -> Dict[str, Any]:
        ic = await ice.now_playing()
        current_title = None
        if isinstance(ic, dict) and ic.get("ok"):
            current_title = ic.get("title")

        # Primary: scheduler NEXT lines (you asked to drive upcoming from this)
        upcoming_sched = docker_client.compute_upcoming_from_scheduler_next(
            scheduler_container=settings.scheduler_container,
            current_title=current_title,
            n=n,
            tail=2500,
        )

        # Secondary/compat: old engine preprocess list (titles only) kept as extra info
        upcoming_engine = docker_client.compute_upcoming_from_preprocess(
            engine_container=settings.engine_container,
            current_title=current_title,
            n=n,
            tail=2500,
        )

        # Provide both representations:
        # - upcoming: list[{title,playlist,ts}] from scheduler
        # - upcoming_titles: list[str] for old UI patterns / debugging
        upcoming_list: List[Dict[str, Any]] = []
        if isinstance(upcoming_sched, dict) and upcoming_sched.get("ok"):
            u = upcoming_sched.get("upcoming") or []
            if isinstance(u, list):
                upcoming_list = [x for x in u if isinstance(x, dict)]

        upcoming_titles: List[str] = []
        if isinstance(upcoming_engine, dict) and upcoming_engine.get("ok"):
            u2 = upcoming_engine.get("upcoming") or []
            if isinstance(u2, list):
                upcoming_titles = [str(x) for x in u2]

        return {
            "ok": True,
            "source": {
                "primary": upcoming_sched.get("source") if isinstance(upcoming_sched, dict) else None,
                "secondary": upcoming_engine.get("source") if isinstance(upcoming_engine, dict) else None,
            },
            "current_title": current_title,
            "upcoming": upcoming_list,
            "upcoming_titles": upcoming_titles,
            "debug": {
                "scheduler": upcoming_sched,
                "engine_preprocess": upcoming_engine,
            },
        }

    return app
