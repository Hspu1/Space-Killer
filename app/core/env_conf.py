from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"
CFG = SettingsConfigDict(
    env_file=ENV_FILE, env_file_encoding='utf-8', extra="ignore"
)


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
    tg_session_timeout: int = 86400

    @property
    def telegram_bot_id(self) -> str:
        return self.telegram_bot_token.split(':')[0]


class ServerSettings(BaseSettings):
    model_config = CFG
    run_host: str = "127.0.0.1"
    run_port: int = 8000
    run_reload: bool = False

    allowed_hosts: list[str] = ("hspu1-the-greatest.loca.lt", )
    forwarded_ips: str = "127.0.0.1"  # + ip balancer
    proxy: str | None = None
    ssl_check: bool = True
    session_lifetime: int = 2592000


class PostgresSettings(BaseSettings):
    model_config = CFG
    db_url: PostgresDsn
    pool_recycle: int = 3600
    pool_size: int = 70  # 4 workers, limit: 1000
    max_overflow: int = 30
    pool_timeout: int = 10


class RedisSettings(BaseSettings):
    model_config = CFG
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 2
    max_connections: int = 500  # 4 workers, limit: 3168
    socket_connect_timeout: int = 5


auth_stg, server_stg, pg_stg, redis_stg = (
    AuthSettings(), ServerSettings(),
    PostgresSettings(), RedisSettings()
)
