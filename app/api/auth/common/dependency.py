from . import AuthProvider


def get_safe_name(data: dict) -> str:
    name = (
        data.get("name") or data.get("real_name") or data.get("display_name") or
        data.get("given_name") or data.get("first_name") or data.get("login") or
        data.get("username") or data.get("twitter_username") or "User"
    )
    return name.split()[0]


def get_safe_email(
        data: dict, provider_name: AuthProvider, provider_user_id: str
) -> tuple[str, bool]:

    raw_email = data.get("email") or data.get("default_email")
    is_verified = data.get("email_verified") is True

    if not is_verified and provider_name.value.lower() == "yandex" and raw_email:
        if raw_email.endswith((
                "@yandex.ru", "@yandex.com", "@ya.ru",
                "@yandex.by", "@yandex.kz", "@yandex.uz",
                "@yandex.az", "@yandex.com.tr"
        )):
            is_verified = True

    if raw_email and is_verified:
        return raw_email, True

    return f"{provider_user_id}@{provider_name.lower()}.user", False
