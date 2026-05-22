"""SQLAlchemy models for D2C order and payment owner tables."""

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
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class D2COrder(Base):
    """D2C order transaction fact.

    Order rows are converted from a cart at checkout time.
    """

    __tablename__ = "d2c_orders"
    __table_args__ = (
        UniqueConstraint("order_no", name="uq_d2c_orders_order_no"),
        UniqueConstraint("cart_id", name="uq_d2c_orders_cart_id"),
        CheckConstraint(
            "item_count >= 0",
            name="ck_d2c_orders_item_count_non_negative",
        ),
        CheckConstraint(
            "subtotal_cents >= 0",
            name="ck_d2c_orders_subtotal_cents_non_negative",
        ),
        Index("ix_d2c_orders_customer_id", "customer_id"),
        Index("ix_d2c_orders_cart_code", "cart_code"),
        Index("ix_d2c_orders_status", "status"),
        Index("ix_d2c_orders_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("d2c_customers.id"),
        nullable=False,
    )
    cart_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("d2c_carts.id"),
        nullable=False,
    )
    cart_code: Mapped[str] = mapped_column(String(96), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    recipient_name: Mapped[str] = mapped_column(String(128), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    shipping_country: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_province: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_city: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_district: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipping_address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    shipping_address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    lines: Mapped[list[D2COrderLine]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list[D2CPayment]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class D2COrderLine(Base):
    """D2C order line with product and SKU snapshots."""

    __tablename__ = "d2c_order_lines"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_d2c_order_lines_quantity_positive"),
        CheckConstraint(
            "unit_price_cents >= 0",
            name="ck_d2c_order_lines_unit_price_cents_non_negative",
        ),
        CheckConstraint(
            "line_subtotal_cents >= 0",
            name="ck_d2c_order_lines_line_subtotal_cents_non_negative",
        ),
        Index("ix_d2c_order_lines_order_id", "order_id"),
        Index("ix_d2c_order_lines_product_id", "product_id"),
        Index("ix_d2c_order_lines_sku_id", "sku_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("d2c_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("d2c_products.id"),
        nullable=False,
    )
    sku_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("d2c_product_skus.id"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    sku_code: Mapped[str] = mapped_column(String(64), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    line_subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    order: Mapped[D2COrder] = relationship(back_populates="lines")


class D2CPayment(Base):
    """D2C payment record prepared for multi-provider payment flows."""

    __tablename__ = "d2c_payments"
    __table_args__ = (
        UniqueConstraint("payment_no", name="uq_d2c_payments_payment_no"),
        CheckConstraint(
            "amount_cents >= 0",
            name="ck_d2c_payments_amount_cents_non_negative",
        ),
        Index("ix_d2c_payments_customer_id", "customer_id"),
        Index("ix_d2c_payments_order_id", "order_id"),
        Index("ix_d2c_payments_order_no", "order_no"),
        Index("ix_d2c_payments_payment_no", "payment_no"),
        Index("ix_d2c_payments_provider", "provider"),
        Index("ix_d2c_payments_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    payment_no: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("d2c_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_no: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_customers.id"),
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="mock",
        server_default="mock",
    )
    payment_method: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="mock",
        server_default="mock",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    provider_trade_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notify_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    order: Mapped[D2COrder] = relationship(back_populates="payments")
