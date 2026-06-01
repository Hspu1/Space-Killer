from sqlalchemy import select, update

from src.infra.persistence.models.models import ProfilesModel
from src.infra.persistence.postgres import PostgresManager


async def pg_resolve_profile(
    pg_manager: PostgresManager, username: str | None = None, user_id: str | None = None
) -> dict | None:
    session_maker = pg_manager.get_session_maker()
    async with session_maker() as session:
        if username:
            stmt = select(ProfilesModel).where(ProfilesModel.username == username)
        elif user_id:
            stmt = select(ProfilesModel).where(ProfilesModel.user_id == user_id)
        else:
            return None

        profile = await session.scalar(stmt)
        if not profile:
            return None

        return {
            "user_id": str(profile.user_id),
            "username": profile.username,
            "nickname": profile.nickname,
            "bio": profile.bio,
            "fid": profile.fid,
        }


async def pg_update_profile(
    pg_manager: PostgresManager,
    user_id: str,
    nickname: str,
    bio: str | None,
) -> None:
    session_maker = pg_manager.get_session_maker()
    async with session_maker.begin() as session:
        await session.execute(
            update(ProfilesModel)
            .where(ProfilesModel.user_id == user_id)
            .values(nickname=nickname, bio=bio)
        )


async def pg_update_avatar(
    pg_manager: PostgresManager,
    user_id: str,
    fid: str | None,
) -> None:
    session_maker = pg_manager.get_session_maker()
    async with session_maker.begin() as session:
        await session.execute(
            update(ProfilesModel).where(ProfilesModel.user_id == user_id).values(fid=fid)
        )
