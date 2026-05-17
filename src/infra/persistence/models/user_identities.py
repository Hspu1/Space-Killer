from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .mixins import TimestampMixin, UUIDv7Mixin

if TYPE_CHECKING:
    from .users import UsersModel


class UserIdentitiesModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "user_identities"

    ####################################################################################

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ####################################################################################

    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="identities")

    ####################################################################################

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_provider_user",
        ),
        Index(
            "idx_identities_user_id",
            "user_id",
        ),
    )
