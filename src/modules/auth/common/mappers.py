from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from src.core.exceptions import ProviderIDMissingError


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


def get_safe_id(user_info: dict[str, Any]) -> str:
    for key in ("id", "sub", "user_id"):
        if value := user_info.get(key):
            return str(value)

    raise ProviderIDMissingError


def get_safe_name(user_info: dict[str, Any]) -> str:
    keys = (
        "name",
        "real_name",
        "display_name",
        "given_name",
        "first_name",
        "login",
        "username",
        "twitter_username",
    )
    full_name = next((user_info.get(k) for k in keys if user_info.get(k)), "User")
    return str(full_name).strip().split(maxsplit=1)[0]


def get_safe_user_info(user_info: dict[str, Any], provider: AuthProvider) -> SafeUserInfo:
    email = (
        None
        if provider == AuthProvider.GITHUB
        else (user_info.get("email") or user_info.get("default_email") or "")
        .lower()
        .strip()
    )

    provider_safe_id = get_safe_id(user_info=user_info)
    return SafeUserInfo(
        id=provider_safe_id,
        name=get_safe_name(user_info=user_info),
        email=email if email else f"{provider_safe_id}@{provider.value.lower()}.user",
        email_verified=user_info.get("email_verified", False),
    )
