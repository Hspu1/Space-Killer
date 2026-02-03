from authlib.integrations.starlette_client import OAuth

from app.core import stg


stackoverflow_oauth = OAuth()
stackoverflow_oauth.register(
    name='stackoverflow',
    client_id=stg.stackoverflow_client_id,
    client_secret=stg.stackoverflow_client_secret,
    authorize_url='https://stackoverflow.com/oauth',
    access_token_url='https://stackoverflow.com/oauth/access_token',
    api_base_url='https://api.stackexchange.com',
    client_kwargs={
        'scope': 'no_expiry',
        'token_endpoint_auth_method': 'client_secret_post'
    },
)
