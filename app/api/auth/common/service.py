import logging
import time
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import or_, select

from .schemas import AuthProvider
from app.infra.postgres.service import pg_service
from app.infra.postgres.models import UsersModel, UserIdentitiesModel
from app.utils import Colors

logger = logging.getLogger(__name__)


async def get_user_id(user_info: dict, provider: AuthProvider, provider_user_id: str) -> str:
    start_time = time.perf_counter()
    session_maker = pg_service.get_session_maker()
    async with session_maker.begin() as session:
        stmt = (
            select(UserIdentitiesModel.user_id)
            .where(
                UserIdentitiesModel.provider == provider,
                UserIdentitiesModel.provider_user_id == provider_user_id
            )
        )

        res = await session.execute(stmt)
        if user_id := res.scalar():
            if logger.isEnabledFor(logging.DEBUG):
                dur_ms = (time.perf_counter() - start_time) * 1000
                logger.debug(
                    "%s[DB] READ%s user_id=%s...: total %s%.2fms%s",
                    Colors.PURPLE, Colors.RESET, str(user_id)[:8],
                    Colors.YELLOW, dur_ms, Colors.RESET
                )
            return str(user_id)

        verify_email = datetime.now(timezone.utc) \
            if user_info.get("email_verified") else None

        stmt = insert(UsersModel).values(
            email=user_info["email"],
            name=user_info.get("name"),
            email_verification_at=verify_email
        )
        user_upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['email'],
            set_={'name': stmt.excluded.name},
            where=or_(
                bool(user_info.get("email_verified")),
                UsersModel.email_verification_at.is_not(None)
            )
        ).returning(UsersModel.id)
        user_id = (await session.execute(user_upsert_stmt)).scalar_one()

        identity_upsert_stmt = (
            insert(UserIdentitiesModel).values(
                user_id=user_id, provider=provider,
                provider_user_id=provider_user_id
            ).on_conflict_do_nothing()
        )

        await session.execute(identity_upsert_stmt)

    dur_ms = (time.perf_counter() - start_time) * 1000
    logger.debug(
        "%s[DB] WRITE/UPSERT%s user=%s: total %s%.2fms%s",
        Colors.PURPLE, Colors.RESET, user_info["email"],
        Colors.YELLOW, dur_ms, Colors.RESET
    )

    return str(user_id)
