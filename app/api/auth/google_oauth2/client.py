from authlib.integrations.starlette_client import OAuth

from app.core.env_conf import stg
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

google_oauth = OAuth()
google_oauth.register(
    name='google',
    client_id=stg.google_client_id,
    client_secret=stg.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
        'timeout': 10.0  # sec
    }
)
