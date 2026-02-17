import logging
from time import perf_counter
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import case, select

from .schemas import AuthProvider
from app.infra.postgres.service import PostgresService
from app.infra.postgres.models import UsersModel, UserIdentitiesModel
from app.utils import Colors

logger = logging.getLogger(__name__)


async def get_user_id(
        pg_svc: PostgresService, user_info: dict, provider: AuthProvider
) -> str:
    start_time = perf_counter()
    session_maker = pg_svc.get_session_maker()
    async with session_maker() as session:
        stmt = (
            select(UserIdentitiesModel.user_id)
            .where(
                UserIdentitiesModel.provider == provider,
                UserIdentitiesModel.provider_user_id == user_info["id"]
            )
        )

        res = await session.execute(stmt)
        if user_id := res.scalar():
            if logger.isEnabledFor(logging.DEBUG):
                dur_ms = (perf_counter() - start_time) * 1000
                logger.debug(
                    "%s[DB] READ%s user_id=%s...: total %s%.2fms%s",
                    Colors.PURPLE, Colors.RESET, str(user_id)[:8],
                    Colors.YELLOW, dur_ms, Colors.RESET
                )
            return str(user_id)

    async with session.begin():
        verify_email = datetime.now(timezone.utc) \
            if user_info["email_verified"] else None

        stmt = insert(UsersModel).values(
            email=user_info["email"], name=user_info["name"],
            email_verification_at=verify_email
        )
        user_upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["email"],
            set_={
                "name": stmt.excluded.name,
                "email_verification_at": case(
                    (user_info.get("email_verified") is True,
                     stmt.excluded.email_verification_at),
                    else_=UsersModel.email_verification_at
                )
            }
        ).returning(UsersModel.id)

        user_id = (await session.execute(user_upsert_stmt)).scalar_one()
        identity_upsert_stmt = (
            insert(UserIdentitiesModel).values(
                user_id=user_id, provider=provider,
                provider_user_id=user_info["id"]
            ).on_conflict_do_nothing()
        )
        await session.execute(identity_upsert_stmt)

    dur_ms = (perf_counter() - start_time) * 1000
    logger.debug(
        "%s[DB] WRITE/UPSERT%s user=%s: total %s%.2fms%s",
        Colors.PURPLE, Colors.RESET, user_info["email"],
        Colors.YELLOW, dur_ms, Colors.RESET
    )

    return str(user_id)
