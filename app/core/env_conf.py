from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding='utf-8', extra="ignore"
    )

    client_id: str
    client_secret: str
    session_secret_key: str
    db_url: str


stg = Settings()
