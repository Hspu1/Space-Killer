import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .mixins import TimestampMixin, UUIDv7Mixin


class UserStatus(enum.Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    BANNED = "banned"


class UsersModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False
    )
    email_verification_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    identities: Mapped[list["UserIdentitiesModel"]] = relationship(
        "UserIdentitiesModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    profile: Mapped["ProfilesModel"] = relationship(
        "ProfilesModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserIdentitiesModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "user_identities"

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="identities")

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


class ProfilesModel(Base, TimestampMixin):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str] = mapped_column(String(20), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fid: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="profile")

    __table_args__ = (
        Index("uq_profiles_username_lowercase", func.lower(username), unique=True),
        {"postgresql_with": {"fillfactor": 85}},  # consider HOT ratio
    )
