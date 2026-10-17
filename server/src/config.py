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
    bailian_rag_base_url: str | None = os.getenv("BAILIAN_RAG_BASE_URL")
    bailian_rag_index_id: str | None = os.getenv("BAILIAN_RAG_INDEX_ID")
    bailian_rag_top_k: int = int(os.getenv("BAILIAN_RAG_TOP_K", "5"))
    typesafe_api_key: str | None = os.getenv("TYPESAFE_API_KEY")
    jev_base_url: str = os.getenv("JEV_BASE_URL", "https://api.typesafe.ai")
    jev_model: str = os.getenv("JEV_MODEL", "jev-latest")
    jev_timeout_seconds: float = float(os.getenv("JEV_TIMEOUT_SECONDS", "10"))
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "personal-workbench-dev")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "personal_workbench")
    mysql_echo: bool = _as_bool(os.getenv("MYSQL_ECHO", "false"))


settings = Settings()
