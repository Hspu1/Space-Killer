from authlib.integrations.starlette_client import OAuth

from app.core.env_conf import auth_stg, server_stg


client_params = {
    'scope': 'user:email',
    'timeout': auth_stg.auth_timeout,
    'verify': server_stg.ssl_check
}
if server_stg.proxy:
    client_params['proxy'] = server_stg.proxy


github_oauth = OAuth()
github_oauth.register(
    name='github',
    client_id=auth_stg.github_client_id,
    client_secret=auth_stg.github_client_secret,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs=client_params
)
