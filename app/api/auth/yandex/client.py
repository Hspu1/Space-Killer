from authlib.integrations.starlette_client import OAuth

from app.core.env_conf import auth_stg

yandex_oauth = OAuth()
yandex_oauth.register(
    name="yandex",
    client_id=auth_stg.yandex_client_id,
    client_secret=auth_stg.yandex_client_secret,
    authorize_url="https://oauth.yandex.ru/authorize",
    access_token_url="https://oauth.yandex.ru/token",  # noqa: S106
    api_base_url="https://login.yandex.ru/",
    client_kwargs={
        "scope": "login:email login:info",
        "token_endpoint_auth_method": "client_secret_post",
        "timeout": auth_stg.auth_timeout,
        "code_challenge_method": "S256",
    },
)
