from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from .mixins import TimestampMixin, UUIDv7Mixin


class UsersModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verification_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

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

    __table_args__ = (
        Index(
            "uq_active_users_email",
            "email",
            unique=True,
            postgresql_where=is_active.is_(True),
        ),
    )


class UserIdentitiesModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "user_identities"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

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


class ProfilesModel(Base, TimestampMixin, UUIDv7Mixin):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["UsersModel"] = relationship("UsersModel", back_populates="profile")

    __table_args__ = (Index("uq_profiles_username", "username", unique=True),)
