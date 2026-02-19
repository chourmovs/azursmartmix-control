from __future__ import annotations

import logging

from pythonjsonlogger import jsonlogger
from fastapi import FastAPI
from nicegui import app, ui

from azursmartmix_control.config import get_settings
from azursmartmix_control.api import create_api
from azursmartmix_control.ui import ControlUI


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.handlers = [handler]


def main() -> int:
    setup_logging()
    settings = get_settings()

    api_app: FastAPI = create_api(settings)

    # Mount FastAPI under /api so NiceGUI and API share one server/port
    app.mount(settings.api_prefix, api_app)

    # Build NiceGUI UI
    ui_builder = ControlUI(settings)
    ui_builder.build()

    ui.run(
        host=settings.ui_host,
        port=settings.ui_port,
        reload=False,
        title="AzurSmartMix Control",
        show=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
