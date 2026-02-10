from . import AuthProvider

YANDEX_DOMAINS = (
    "@yandex.ru", "@yandex.com", "@ya.ru", "@yandex.by",
    "@yandex.kz", "@yandex.uz", "@yandex.az", "@yandex.com.tr"
)


def get_safe_id(data: dict) -> str:
    for key in ("id", "sub", "user_id"):
        if value := data.get(key):
            return str(value)

    raise ValueError("Provider data is missing a unique ID")


def get_safe_name(data: dict) -> str:
    keys = (
        "name", "real_name", "display_name", "given_name",
        "first_name", "login", "username", "twitter_username"
    )
    full_name = next((data.get(k) for k in keys if data.get(k)), "User")
    return str(full_name).strip().split(maxsplit=1)[0]


def get_safe_email(
        data: dict, provider_name: AuthProvider, provider_user_id: str
) -> tuple[str, bool]:

    email = (data.get("email") or data.get("default_email") or "").lower().strip()
    is_verified = data.get("email_verified") is True
    provider = provider_name.value.lower()

    if not is_verified and provider == "yandex" and email.endswith(YANDEX_DOMAINS):
        is_verified = True

    if email and is_verified:
        return email, True

    return f"{provider_user_id}@{provider}.user", False
