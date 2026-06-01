from sqlalchemy import select

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

        result = await session.execute(stmt)
        row = result.first()
        if not row:
            return None

        return {
            "user_id": str(row.user_id),
            "username": row.username,
            "nickname": row.nickname,
            "bio": row.bio,
            "fid": row.fid,
        }
