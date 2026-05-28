"""Promotion and coupon runtime usage fact models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm import Base


class CustomerCoupon(Base):
    """Customer coupon usage fact written by checkout.

    Promotion and coupon runtime facts live in d2c-api.
    d2c-api stores only runtime usage facts and published snapshots.
    """

    __tablename__ = "d2c_customer_coupons"
    __table_args__ = (
        UniqueConstraint(
            "customer_coupon_code",
            name="uq_d2c_customer_coupons_code",
        ),
        CheckConstraint(
            "used_at IS NULL OR claimed_at IS NULL OR used_at >= claimed_at",
            name="ck_d2c_customer_coupons_used_after_claimed",
        ),
        Index("ix_d2c_customer_coupons_customer_id", "customer_id"),
        Index("ix_d2c_customer_coupons_status", "status"),
        Index("ix_d2c_customer_coupons_publish_version", "publish_version"),
        Index("ix_d2c_customer_coupons_coupon_code", "coupon_code"),
        Index("ix_d2c_customer_coupons_promotion_code", "promotion_code"),
        Index("ix_d2c_customer_coupons_order_no", "order_no"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_coupon_code: Mapped[str] = mapped_column(String(96), nullable=False)
    publish_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    coupon_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    coupon_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    coupon_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    promotion_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    promotion_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    promotion_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    promotion_discount_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    promotion_discount_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="claimed",
        server_default="claimed",
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    order_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("d2c_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    order_no: Mapped[str | None] = mapped_column(String(32), nullable=True)
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
