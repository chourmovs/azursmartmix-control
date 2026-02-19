from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Runtime settings for the control plane.

    v1 is read-only:
    - reads a config YAML file (optional)
    - reads docker container status/logs via docker socket (ro)
    - proxies scheduler API for now/upcoming
    """

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    # API wiring
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    # UI bind
    ui_host: str = Field(default="0.0.0.0", alias="UI_HOST")
    ui_port: int = Field(default=8088, alias="UI_PORT")

    # Targets
    engine_container: str = Field(default="azursmartmix_engine", alias="ENGINE_CONTAINER")
    scheduler_container: str = Field(default="azursmartmix_scheduler", alias="SCHEDULER_CONTAINER")

    # Scheduler API base URL
    sched_base_url: str = Field(default="http://azursmartmix_scheduler:8001", alias="SCHED_BASE_URL")

    # Config file exposed read-only
    config_path: str = Field(default="/config/config.yml", alias="CONFIG_PATH")

    # Logs
    log_tail_lines_default: int = Field(default=400, alias="LOG_TAIL_LINES_DEFAULT")
    log_tail_lines_max: int = Field(default=2000, alias="LOG_TAIL_LINES_MAX")


def get_settings() -> Settings:
    return Settings()
