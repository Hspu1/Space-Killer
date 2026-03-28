from enum import StrEnum

from pydantic import BaseModel


class AuthProvider(StrEnum):
    GOOGLE = "google"
    GITHUB = "github"
    TELEGRAM = "telegram"
    YANDEX = "yandex"
    STACKOVERFLOW = "stackoverflow"


class SafeUserInfo(BaseModel):
    id: str
    name: str
    email: str
    email_verified: bool
