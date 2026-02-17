from typing import Any

from app.api.auth.common.schemas import AuthProvider

YANDEX_DOMAINS = (
    "@yandex.ru", "@yandex.com", "@ya.ru", "@yandex.by",
    "@yandex.kz", "@yandex.uz", "@yandex.az", "@yandex.com.tr"
)


def get_safe_id(user_info: dict) -> str:
    for key in ("id", "sub", "user_id"):
        if value := user_info.get(key):
            return str(value)

    raise ValueError("Provider data is missing a unique ID")


def get_safe_name(user_info: dict) -> str:
    keys = (
        "name", "real_name", "display_name", "given_name",
        "first_name", "login", "username", "twitter_username"
    )
    full_name = next((user_info.get(k) for k in keys if user_info.get(k)), "User")
    return str(full_name).strip().split(maxsplit=1)[0]


def get_safe_info(user_info: dict[str, Any], provider: AuthProvider) -> dict[str, str | bool]:
    email = (user_info.get("email") or user_info.get("default_email") or "").lower().strip()
    is_verified = user_info.get("email_verified") is True
    provider = provider.value.lower()

    if not is_verified and provider == "yandex" and email.endswith(YANDEX_DOMAINS):
        is_verified = True

    provider_safe_id = get_safe_id(user_info=user_info)
    result = {
        "id": provider_safe_id, "name": get_safe_name(user_info=user_info),
        "email": email if email else f"{provider_safe_id}@{provider}.user",
        "email_verified": True if is_verified else False
    }
    return result
