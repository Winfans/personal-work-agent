"""Runtime configuration loaded from environment variables."""

from dataclasses import dataclass
import os


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Personal Work Agent Backend")
    environment: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = _as_bool(os.getenv("APP_DEBUG", "false"))


settings = Settings()
