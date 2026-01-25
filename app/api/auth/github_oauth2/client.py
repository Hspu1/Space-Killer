# from authlib.integrations.starlette_client import OAuth
#
# from app.core.env_conf import stg
# import os
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
#
# github_oauth = OAuth()
# github_oauth.register(
#     name='github',
#     client_id=stg.github_client_id,
#     client_secret=stg.github_client_secret,
#     access_token_url='https://github.com/login/oauth/access_token',
#     authorize_url='https://github.com/login/oauth/authorize',
#     api_base_url='https://api.github.com/',
#     client_kwargs={
#         'scope': 'user:email',
#         'timeout': 10.0,  # sec
#         'verify': False,  # ONLY FOR DEVELOPMENT
#         'trust_env': False  # CHTOBLYAT
#     }
# )
