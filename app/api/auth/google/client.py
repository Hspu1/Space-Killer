from authlib.integrations.starlette_client import OAuth

from app.core.env_conf import auth_stg


google_oauth = OAuth()
google_oauth.register(
    name='google',
    client_id=auth_stg.google_client_id,
    client_secret=auth_stg.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
        'timeout': auth_stg.auth_timeout
    }
)
