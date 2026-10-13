"""Runtime configuration loaded from environment variables."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Personal Work Agent Backend")
    environment: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("APP_HOST", "127.0.0.1")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = _as_bool(os.getenv("APP_DEBUG", "false"))
    bailian_api_key: str | None = os.getenv("DASHSCOPE_API_KEY")
    bailian_base_url: str = os.getenv(
        "BAILIAN_BASE_URL",
        "https://ws-rco9ybd863lyd687.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    )
    bailian_model: str = os.getenv("BAILIAN_MODEL", "deepseek-v4.1-flash")


settings = Settings()
