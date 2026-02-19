from __future__ import annotations

import os
from typing import Any, Dict

import yaml
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from azursmartmix_control.config import Settings
from azursmartmix_control.docker_client import DockerClient
from azursmartmix_control.scheduler_client import SchedulerClient


def create_api(settings: Settings) -> FastAPI:
    """Build the FastAPI app providing read-only endpoints."""
    app = FastAPI(title="AzurSmartMix Control API", version="0.1.0")

    docker_client = DockerClient()
    sched = SchedulerClient(settings.sched_base_url)

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"ok": True}

    @app.get("/status")
    def status() -> Dict[str, Any]:
        return docker_client.runtime_summary(settings.engine_container, settings.scheduler_container)

    @app.get("/config")
    def read_config() -> Dict[str, Any]:
        path = settings.config_path
        if not path or not os.path.exists(path):
            return {"present": False, "path": path, "data": None}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return {"present": True, "path": path, "data": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read YAML: {e}")

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

    @app.get("/scheduler/health")
    async def scheduler_health() -> JSONResponse:
        data = await sched.health()
        return JSONResponse(data)

    @app.get("/scheduler/now")
    async def scheduler_now() -> JSONResponse:
        data = await sched.now_playing()
        return JSONResponse(data)

    @app.get("/scheduler/upcoming")
    async def scheduler_upcoming(n: int = Query(10, ge=1, le=50)) -> JSONResponse:
        data = await sched.upcoming(n=n)
        return JSONResponse(data)

    return app
