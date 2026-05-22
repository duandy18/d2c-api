from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm import Base


class BackofficePage(Base):
    __tablename__ = "d2c_backoffice_pages"
    __table_args__ = (
        UniqueConstraint(
            "page_code",
            name="uq_d2c_backoffice_pages_page_code",
        ),
        Index("ix_d2c_backoffice_pages_parent_code", "parent_code"),
        Index("ix_d2c_backoffice_pages_route_path", "route_path"),
        Index("ix_d2c_backoffice_pages_sort_order", "sort_order"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    page_code: Mapped[str] = mapped_column(String(160), nullable=False)
    parent_code: Mapped[str | None] = mapped_column(String(160), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    route_path: Mapped[str] = mapped_column(String(240), nullable=False)
    component_key: Mapped[str] = mapped_column(String(160), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    implementation_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="planned",
    )
    data_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="placeholder",
    )
    required_permission: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
