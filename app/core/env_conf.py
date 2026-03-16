from functools import cached_property
from hashlib import sha256
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
CFG = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


class AuthSettings(BaseSettings):
    model_config = CFG
    auth_timeout: float = 5.0
    google_client_id: str = Field(default=...)
    google_client_secret: str = Field(default=...)

    github_client_id: str = Field(default=...)
    github_client_secret: str = Field(default=...)

    yandex_client_id: str = Field(default=...)
    yandex_client_secret: str = Field(default=...)

    stackoverflow_api_key: str = Field(default=...)
    stackoverflow_client_id: str = Field(default=...)
    stackoverflow_client_secret: str = Field(default=...)

    telegram_bot_token: str = Field(default=...)
    tg_session_timeout: int = 300

    @cached_property
    def telegram_bot_id(self) -> str:
        return self.telegram_bot_token.split(":")[0]

    @cached_property
    def secret_key(self) -> bytes:
        return sha256(self.telegram_bot_token.encode()).digest()


class ServerSettings(BaseSettings):
    model_config = CFG
    run_host: str = "127.0.0.1"
    run_port: int = 8000

    allowed_hosts: tuple[str, ...] = ("hspu1-the-greatest.loca.lt", "127.0.0.1")
    forwarded_ips: str = "127.0.0.1"  # + ip balancer
    proxy: str | None = None  # for GitHub (check .env)
    ssl_check: bool = True
    session_lifetime: int = 604_800


class PostgresSettings(BaseSettings):
    model_config = CFG
    db_url: Annotated[PostgresDsn, AfterValidator(str)] = Field(default=...)
    pool_recycle: int = 1800
    pool_size: int = 15
    max_overflow: int = 5
    pool_timeout: int = 5


class RedisSettings(BaseSettings):
    model_config = CFG
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 2

    @cached_property
    def db_url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"

    max_connections: int = 100
    socket_timeout: float = 0.5
    socket_connect_timeout: float = 1.5
    health_check_interval: int = 30


class HTTPSettings(BaseSettings):
    model_config = CFG
    max_connections: int = 100
    max_keepalive_connections: int = 30
    keepalive_expiry: float = 20.0
    warmup_urls: tuple[str, ...] = (
        "https://github.com/login/oauth/access_token",
        "https://api.github.com/user",
    )


auth_stg, server_stg, pg_stg, redis_stg, http_stg = (
    AuthSettings(),
    ServerSettings(),
    PostgresSettings(),
    RedisSettings(),
    HTTPSettings(),
)
