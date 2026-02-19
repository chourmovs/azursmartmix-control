from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from azursmartmix_control.config import Settings
from azursmartmix_control.docker_client import DockerClient
from azursmartmix_control.scheduler_client import SchedulerClient
from azursmartmix_control.compose_reader import get_service_env
from azursmartmix_control.icecast_client import IcecastClient


def create_api(settings: Settings) -> FastAPI:
    """Build the FastAPI app providing read-only endpoints."""
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

    # --- compose env (your "config") ---
    @app.get("/compose/env")
    def compose_env(service: str = Query(..., description="docker-compose service name")) -> Dict[str, Any]:
        return get_service_env(settings.compose_path, service)

    @app.get("/compose/engine_env")
    def compose_engine_env() -> Dict[str, Any]:
        return get_service_env(settings.compose_path, settings.compose_service_engine)

    @app.get("/compose/scheduler_env")
    def compose_scheduler_env() -> Dict[str, Any]:
        return get_service_env(settings.compose_path, settings.compose_service_scheduler)

    # --- logs ---
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

    # --- scheduler proxy ---
    @app.get("/scheduler/health")
    async def scheduler_health() -> JSONResponse:
        data = await sched.health()
        return JSONResponse(data)

    @app.get("/scheduler/upcoming")
    async def scheduler_upcoming(n: int = Query(10, ge=1, le=50)) -> JSONResponse:
        data = await sched.upcoming(n=n)
        return JSONResponse(data)

    # --- now playing ---
    @app.get("/icecast/now")
    async def icecast_now() -> JSONResponse:
        data = await ice.now_playing()
        return JSONResponse(data)

    @app.get("/now_playing")
    async def now_playing() -> JSONResponse:
        """Unified now playing: prefer Icecast (authoritative), fallback to engine logs."""
        ice_data = await ice.now_playing()
        if isinstance(ice_data, dict) and ice_data.get("ok"):
            return JSONResponse({"ok": True, "preferred": "icecast", "icecast": ice_data})

        log_data = docker_client.best_effort_now_playing_from_logs(settings.engine_container)
        return JSONResponse({"ok": bool(log_data.get("ok")), "preferred": "engine_logs", "icecast": ice_data, "engine_logs": log_data})

    return app
