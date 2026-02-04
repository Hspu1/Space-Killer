from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding='utf-8', extra="ignore"
    )

    proxy: str | None
    ssl_check: bool = True

    db_url: str

    google_client_id: str
    google_client_secret: str

    github_client_id: str
    github_client_secret: str

    telegram_bot_token: str

    @property
    def telegram_bot_id(self) -> str:
        return self.telegram_bot_token.split(':')[0]

    yandex_client_id: str
    yandex_client_secret: str

    stackoverflow_api_key: str
    stackoverflow_client_id: str
    stackoverflow_client_secret: str

    session_lifetime: int = 2592000
    allowed_hosts: list[str] = ["127.0.0.1", "localhost"]  # + localtunnel/domain
    forwarded_ips: str = "127.0.0.1"  # + ip balancer

    run_host: str = "127.0.0.1"
    run_port: int = 8000
    run_reload: bool = False


stg = Settings()
