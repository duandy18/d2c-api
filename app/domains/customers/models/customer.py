"""Customer domain ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
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


class Customer(Base):
    __tablename__ = "d2c_customers"
    __table_args__ = (
        UniqueConstraint("customer_code", name="uq_d2c_customers_customer_code"),
        UniqueConstraint("email", name="uq_d2c_customers_email"),
        UniqueConstraint("phone", name="uq_d2c_customers_phone"),
        Index("ix_d2c_customers_customer_code", "customer_code"),
        Index("ix_d2c_customers_email", "email"),
        Index("ix_d2c_customers_phone", "phone"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_code: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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


class CustomerPasswordCredential(Base):
    __tablename__ = "d2c_customer_password_credentials"
    __table_args__ = (
        UniqueConstraint("customer_id", name="uq_d2c_customer_password_credentials_customer_id"),
        Index("ix_d2c_customer_password_credentials_customer_id", "customer_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    password_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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


class CustomerAddress(Base):
    __tablename__ = "d2c_customer_addresses"
    __table_args__ = (Index("ix_d2c_customer_addresses_customer_id", "customer_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False, default="US")
    province: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(240), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(240), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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


class CustomerSession(Base):
    __tablename__ = "d2c_customer_sessions"
    __table_args__ = (
        UniqueConstraint("session_token_hash", name="uq_d2c_customer_sessions_token_hash"),
        Index("ix_d2c_customer_sessions_customer_id", "customer_id"),
        Index("ix_d2c_customer_sessions_token_hash", "session_token_hash"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
