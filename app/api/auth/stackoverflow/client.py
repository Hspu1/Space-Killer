from authlib.integrations.starlette_client import OAuth

from app.core.env_conf import auth_stg


stackoverflow_oauth = OAuth()
stackoverflow_oauth.register(
    name='stackoverflow',
    client_id=auth_stg.stackoverflow_client_id,
    client_secret=auth_stg.stackoverflow_client_secret,
    authorize_url='https://stackoverflow.com/oauth',
    access_token_url='https://stackoverflow.com/oauth/access_token',
    api_base_url='https://api.stackexchange.com',
    client_kwargs={
        'scope': 'no_expiry',
        'token_endpoint_auth_method': 'client_secret_post',
        "timeout": auth_stg.auth_timeout,
    },
)
