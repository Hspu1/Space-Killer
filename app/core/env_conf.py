from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding='utf-8', extra="ignore"
    )

    session_secret_key: str
    csrf_secret_key: str
    proxy: str | None
    ssl_check: bool = True
    db_url: str
    google_client_id: str
    google_client_secret: str
    github_client_id: str
    github_client_secret: str
    telegram_bot_token: str
    yandex_client_id: str
    yandex_client_secret: str
    stackoverflow_api_key: str
    stackoverflow_client_id: str
    stackoverflow_client_secret: str

    @property
    def telegram_bot_id(self) -> str:
        return self.telegram_bot_token.split(':')[0]


stg = Settings()
