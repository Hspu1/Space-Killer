# from datetime import datetime, timezone
# from typing import Optional
#
# from authlib.integrations.starlette_client import OAuthError
# from fastapi import Request
# from fastapi.responses import RedirectResponse
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.exc import IntegrityError
#
# from app.api.auth.github_oauth2.client import github_oauth
# from app.core import UsersModel, UserIdentitiesModel
# from app.core.db.database import async_session_maker
#
#
# async def get_identity(session: AsyncSession, provider_user_id: str) -> Optional[UserIdentitiesModel]:
#     stmt = select(UserIdentitiesModel).where(
#         UserIdentitiesModel.provider == "github",
#         UserIdentitiesModel.provider_user_id == provider_user_id
#     )
#     return (await session.execute(stmt)).scalar_one_or_none()
#
#
# async def get_email(session: AsyncSession, email: str) -> Optional[UsersModel]:
#     stmt = select(UsersModel).where(UsersModel.email == email)
#     return (await session.execute(stmt)).scalar_one_or_none()
#
#
# async def get_user_id(user_info: dict) -> str:
#     async with async_session_maker.begin() as session:
#         provider_user_id = str(user_info["id"])
#
#         identity = await get_identity(session, provider_user_id)
#         if identity:
#             return str(identity.user_id)
#
#         user = await get_email(session, user_info["email"])
#         email_verification = datetime.now(timezone.utc) if user_info.get("verified") else None
#
#         if not user:
#             try:
#                 async with session.begin_nested():
#                     user = UsersModel(
#                         email=user_info["email"],
#                         full_name=user_info.get("name") or user_info.get("login") or "GitHub User",
#                         email_verification_at=email_verification
#                     )
#                     session.add(user)
#                     await session.flush()
#
#             except IntegrityError:
#                 user = await get_email(session, user_info["email"])
#
#         new_identity = UserIdentitiesModel(
#             user_id=user.id,
#             provider="github",
#             provider_user_id=provider_user_id
#         )
#
#         session.add(new_identity)
#         return str(user.id)
#
#
# async def github_callback_handling(request: Request) -> RedirectResponse:
#     if request.query_params.get("error"):
#         return RedirectResponse(url="/?msg=access_denied")
#
#     try:
#         token = await github_oauth.github.authorize_access_token(request)
#
#         resp = await github_oauth.github.get('user', token=token)
#         user_info = resp.json()
#
#         if user_info:
#             request.session.clear()
#             user_id = await get_user_id(user_info)
#             request.session['user_id'] = user_id
#             request.session['given_name'] = user_info.get("name") or user_info.get("login")
#
#         return RedirectResponse(url='/welcome')
#
#     except OAuthError:
#         return RedirectResponse(url="/?msg=session_expired")
