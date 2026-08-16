"""AI-CCTV Sentinel — configuration loading foundation.

Task 2 scope: this module only loads and exposes configuration. It
does not implement any business logic (risk scoring, alert routing,
etc.) — those consume this configuration in later tasks.

Design rules this module follows:
    - Nothing here is hard-coded application behavior; all tunable
      values live in configs/*.yaml.
    - Secrets (e.g. RTSP credentials) are never read from YAML — only
      from environment variables (typically loaded from a local,
      git-ignored .env file). YAML may reference an env var name via
      a `*_env` key, but never a literal secret value.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"


class Settings(BaseSettings):
    """Process-wide settings sourced from environment variables / .env.

    This intentionally stays small: it covers app-level wiring
    (host/port/env name) plus secret *references*. Structural,
    non-secret configuration (thresholds, zones, alert policy, ...)
    lives in the YAML files under configs/ and is loaded separately
    via `load_yaml_config`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI-CCTV Sentinel"
    app_env: str = "development"
    app_version: str = "0.1.0"

    host: str = "127.0.0.1"
    port: int = 8000

    log_level: str = "INFO"

    ai_device: str = "auto"
    yolo_model: str = "yolo26n.pt"
    yolo_confidence: float = 0.50

    # Deliberately left blank / optional in Task 2 — no real database,
    # broker, or cloud project is provisioned yet.
    database_url: str | None = None
    firebase_project_id: str | None = None
    mqtt_broker_url: str | None = None
    mqtt_username: str | None = None
    mqtt_password: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached process-wide settings."""

    return Settings()


def load_yaml_config(name: str, config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    """Load a single YAML config file by name (without extension).

    Example:
        risk_config = load_yaml_config("risk")  # reads configs/risk.yaml
    """

    path = config_dir / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def resolve_env_reference(config_value: dict[str, Any], key: str = "url_env") -> str | None:
    """Resolve a `<field>_env` style reference to its environment value.

    Camera stream URLs (and any other secret-shaped config) are stored
    in YAML as a reference to an environment variable name, never as a
    literal value. This helper performs that indirection lookup and
    returns None if the variable isn't set, rather than raising, so
    that architecture code can be exercised before any real camera is
    provisioned.
    """

    env_var_name = config_value.get(key)
    if not env_var_name:
        return None
    return os.environ.get(env_var_name)


@dataclass(frozen=True)
class AppConfig:
    """Aggregated, read-only view of all structural YAML configuration.

    This is a convenience bundle for later tasks (backend startup,
    services) so they can depend on one object instead of loading each
    YAML file individually.
    """

    camera: dict[str, Any]
    video: dict[str, Any]
    model: dict[str, Any]
    risk: dict[str, Any]
    alerts: dict[str, Any]
    system: dict[str, Any]


@lru_cache(maxsize=1)
def load_app_config(config_dir: Path = CONFIG_DIR) -> AppConfig:
    """Load and aggregate all Task-2-defined configuration files."""

    return AppConfig(
        camera=load_yaml_config("camera", config_dir),
        video=load_yaml_config("video", config_dir),
        model=load_yaml_config("model", config_dir),
        risk=load_yaml_config("risk", config_dir),
        alerts=load_yaml_config("alerts", config_dir),
        system=load_yaml_config("system", config_dir),
    )
