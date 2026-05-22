"""Analytics domain ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm import Base


class VisitorSession(Base):
    __tablename__ = "d2c_visitor_sessions"
    __table_args__ = (
        UniqueConstraint("session_code", name="uq_d2c_visitor_sessions_session_code"),
        Index("ix_d2c_visitor_sessions_anonymous_id", "anonymous_id"),
        Index("ix_d2c_visitor_sessions_customer_id", "customer_id"),
        Index("ix_d2c_visitor_sessions_session_code", "session_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_code: Mapped[str] = mapped_column(String(96), nullable=False)
    anonymous_id: Mapped[str] = mapped_column(String(96), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class BehaviorEvent(Base):
    __tablename__ = "d2c_behavior_events"
    __table_args__ = (
        UniqueConstraint("event_code", name="uq_d2c_behavior_events_event_code"),
        Index("ix_d2c_behavior_events_anonymous_id", "anonymous_id"),
        Index("ix_d2c_behavior_events_customer_id", "customer_id"),
        Index("ix_d2c_behavior_events_event_type", "event_type"),
        Index("ix_d2c_behavior_events_occurred_at", "occurred_at"),
        Index("ix_d2c_behavior_events_product_code", "product_code"),
        Index("ix_d2c_behavior_events_session_id", "session_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_code: Mapped[str] = mapped_column(String(96), nullable=False)
    session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_visitor_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    anonymous_id: Mapped[str] = mapped_column(String(96), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    page_path: Mapped[str] = mapped_column(Text, nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    sku_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_metadata: Mapped[dict[str, object] | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
