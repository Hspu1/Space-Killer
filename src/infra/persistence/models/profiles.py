from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .mixins import TimestampMixin, UUIDv7Mixin

if TYPE_CHECKING:
    from .users import UsersModel


class ProfilesModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "profiles"

    ####################################################################################

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ####################################################################################

    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="profile")

    ####################################################################################

    __table_args__ = (Index("uq_profiles_username", "username", unique=True),)
