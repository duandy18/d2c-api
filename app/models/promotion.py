from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
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

from app.models.base import Base


class Promotion(Base):
    __tablename__ = "d2c_promotions"
    __table_args__ = (
        UniqueConstraint("promotion_code", name="uq_d2c_promotions_code"),
        CheckConstraint(
            "discount_value > 0",
            name="ck_d2c_promotions_discount_value_positive",
        ),
        CheckConstraint(
            "discount_type <> 'percentage' OR discount_value <= 100",
            name="ck_d2c_promotions_percentage_value_valid",
        ),
        CheckConstraint(
            "min_order_amount_cents IS NULL OR min_order_amount_cents >= 0",
            name="ck_d2c_promotions_min_order_amount_non_negative",
        ),
        CheckConstraint(
            "max_discount_cents IS NULL OR max_discount_cents >= 0",
            name="ck_d2c_promotions_max_discount_non_negative",
        ),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_promotions_effective_range_valid",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_d2c_promotions_priority_non_negative",
        ),
        Index("ix_d2c_promotions_code", "promotion_code"),
        Index("ix_d2c_promotions_status", "status"),
        Index("ix_d2c_promotions_type", "promotion_type"),
        Index("ix_d2c_promotions_active_range", "is_active", "starts_at", "ends_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    promotion_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    promotion_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    min_order_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_discount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default="USD",
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default="100",
    )
    stackable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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


class PromotionTarget(Base):
    __tablename__ = "d2c_promotion_targets"
    __table_args__ = (
        UniqueConstraint(
            "promotion_id",
            "target_type",
            "target_id",
            "target_code",
            name="uq_d2c_promotion_targets_scope",
        ),
        CheckConstraint(
            "target_type = 'all_store' OR target_id IS NOT NULL OR target_code IS NOT NULL",
            name="ck_d2c_promotion_targets_target_present",
        ),
        Index("ix_d2c_promotion_targets_promotion_id", "promotion_id"),
        Index(
            "ix_d2c_promotion_targets_target",
            "target_type",
            "target_id",
            "target_code",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    promotion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_promotions.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Coupon(Base):
    __tablename__ = "d2c_coupons"
    __table_args__ = (
        UniqueConstraint("coupon_code", name="uq_d2c_coupons_code"),
        CheckConstraint(
            "total_limit IS NULL OR total_limit > 0",
            name="ck_d2c_coupons_total_limit_positive",
        ),
        CheckConstraint(
            "per_customer_limit IS NULL OR per_customer_limit > 0",
            name="ck_d2c_coupons_per_customer_limit_positive",
        ),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_coupons_effective_range_valid",
        ),
        Index("ix_d2c_coupons_code", "coupon_code"),
        Index("ix_d2c_coupons_status", "status"),
        Index("ix_d2c_coupons_promotion_id", "promotion_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    coupon_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    promotion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_promotions.id", ondelete="CASCADE"),
        nullable=False,
    )
    coupon_type: Mapped[str] = mapped_column(String(32), nullable=False)
    total_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_customer_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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


class CustomerCoupon(Base):
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
        Index("ix_d2c_customer_coupons_coupon_id", "coupon_id"),
        Index("ix_d2c_customer_coupons_customer_id", "customer_id"),
        Index("ix_d2c_customer_coupons_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_coupon_code: Mapped[str] = mapped_column(String(96), nullable=False)
    coupon_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_coupons.id", ondelete="CASCADE"),
        nullable=False,
    )
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
