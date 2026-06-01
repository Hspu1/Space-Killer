from time import perf_counter
from typing import TypedDict

from sqlalchemy import select

from src.infra.persistence.models.models import ProfilesModel
from src.infra.persistence.postgres import PostgresManager
from src.utils import log_debug_db


class UserMeta(TypedDict):
    username: str
    avatar_fid: str | None


async def pg_resolve_user_meta(user_id: str, pg_manager: PostgresManager) -> UserMeta:
    start_time = perf_counter()
    session_maker = pg_manager.get_session_maker()
    async with session_maker() as session:
        stmt = select(ProfilesModel.username, ProfilesModel.avatar_fid).where(
            ProfilesModel.user_id == user_id
        )
        result = await session.execute(stmt)
        row = result.one()

        log_debug_db(op="READ", start_time=start_time, detail=f"user_id={user_id[:8]}...")
        return {"username": row[0], "avatar_fid": row[1]}
