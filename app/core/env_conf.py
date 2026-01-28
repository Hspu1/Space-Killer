from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding='utf-8', extra="ignore"
    )

    session_secret_key: str
    db_url: str
    google_client_id: str
    google_client_secret: str
    github_client_id: str
    github_client_secret: str
    telegram_bot_token: str


stg = Settings()
