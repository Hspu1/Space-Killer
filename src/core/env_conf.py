from functools import cached_property
from hashlib import sha256
from pathlib import Path
from typing import Annotated

from pydantic import AfterValidator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
CFG = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


class AuthSettings(BaseSettings):
    model_config = CFG
    auth_timeout: float = 10.0
    google_client_id: str
    google_client_secret: str

    github_client_id: str
    github_client_secret: str

    yandex_client_id: str
    yandex_client_secret: str

    stackoverflow_api_key: str
    stackoverflow_client_id: str
    stackoverflow_client_secret: str

    telegram_bot_token: str
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
    proxy: str | None = None  # for GitHub (check .env) (optional)
    ssl_check: bool = True
    session_lifetime: int = 604_800


class PostgresSettings(BaseSettings):
    model_config = CFG
    db_url: Annotated[PostgresDsn, AfterValidator(str)]
    pool_recycle: int = 1800
    pool_size: int = 50  # !!! 2 granian workers !!!, check limits
    max_overflow: int = 20
    pool_timeout: int = 30


class RedisSettings(BaseSettings):
    model_config = CFG
    host: str = "redis"
    port: int = 6379
    db: int = 0  # !!! - have to be fixed if needed
    password: str | None = None

    @cached_property
    def db_url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"

    max_connections: int = 500  # !!! 2 granian workers !!!, check limits
    socket_timeout: float = 0.5
    socket_connect_timeout: float = 1.5
    health_check_interval: int = 30


class HTTPSettings(BaseSettings):  # for src/infra/auth_http_client.py
    model_config = CFG
    max_connections: int = 25
    max_keepalive_connections: int = 15
    keepalive_expiry: float = 20.0
    warmup_urls: tuple[str, str] = (
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
