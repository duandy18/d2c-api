"""Cart domain ORM models."""

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


class Cart(Base):
    __tablename__ = "d2c_carts"
    __table_args__ = (
        UniqueConstraint("cart_code", name="uq_d2c_carts_cart_code"),
        CheckConstraint(
            "line_count >= 0",
            name="ck_d2c_carts_line_count_non_negative",
        ),
        CheckConstraint(
            "item_count >= 0",
            name="ck_d2c_carts_item_count_non_negative",
        ),
        CheckConstraint(
            "subtotal_cents >= 0",
            name="ck_d2c_carts_subtotal_cents_non_negative",
        ),
        Index("ix_d2c_carts_anonymous_id", "anonymous_id"),
        Index("ix_d2c_carts_cart_code", "cart_code"),
        Index("ix_d2c_carts_customer_id", "customer_id"),
        Index("ix_d2c_carts_session_code", "session_code"),
        Index("ix_d2c_carts_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cart_code: Mapped[str] = mapped_column(String(96), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    anonymous_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    session_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default="USD",
    )
    line_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    item_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    subtotal_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
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


class CartLine(Base):
    __tablename__ = "d2c_cart_lines"
    __table_args__ = (
        UniqueConstraint("cart_id", "sku_id", name="uq_d2c_cart_lines_cart_id_sku_id"),
        Index("ix_d2c_cart_lines_cart_id", "cart_id"),
        Index("ix_d2c_cart_lines_product_id", "product_id"),
        Index("ix_d2c_cart_lines_sku_id", "sku_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cart_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_carts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_product_skus.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default="USD",
    )
    line_subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
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
