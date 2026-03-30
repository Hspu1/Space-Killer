from src.core.env_conf import auth_stg

from .enums import HttpMethods


def github_kwargs(
    http_method: HttpMethods,
    access_token: str = "",
    code: str = "",
    redirect_uri: str = "",
) -> dict:

    if http_method is HttpMethods.POST:
        return {
            "url": "https://github.com/login/oauth/access_token",
            "data": {
                "client_id": auth_stg.github_client_id,
                "client_secret": auth_stg.github_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            "headers": {
                "Accept": "application/json",
                "User-Agent": "Smth-P",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        }

    elif http_method is HttpMethods.GET:
        return {
            "url": "https://api.github.com/user",
            "headers": {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "Smth-P",
            },
        }
