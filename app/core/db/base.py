from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func, DateTime
from uuid6 import uuid7


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """sort_order=999 и sort_order=1000 -> поля о дате в самом конце"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), sort_order=999
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), sort_order=1000
    )


class UUIDv7Mixin:
    """
    default=uuid7 -> SQLA сама идет за одноимённой функцией каждый раз,
    делая ID уникальным + всё чисто и аккуратно смотрится
    sort_order=-1 -> поле с ID в самом начале"""
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7,
        unique=True, nullable=False, sort_order=-1
    )