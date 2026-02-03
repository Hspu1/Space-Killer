from authlib.integrations.starlette_client import OAuth

from app.core import stg


client_params = {
    'scope': 'user:email',
    'timeout': 10.0,
    'verify': stg.ssl_check
}
if stg.proxy:
    client_params['proxy'] = stg.proxy


github_oauth = OAuth()
github_oauth.register(
    name='github',
    client_id=stg.github_client_id,
    client_secret=stg.github_client_secret,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs=client_params
)
