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
    Text,
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
        UniqueConstraint(
            "cart_id",
            "publish_version",
            "offer_code",
            name="uq_d2c_cart_lines_cart_offer",
        ),
        Index("ix_d2c_cart_lines_cart_id", "cart_id"),
        Index("ix_d2c_cart_lines_publish_version", "publish_version"),
        Index("ix_d2c_cart_lines_offer_code", "offer_code"),
        Index("ix_d2c_cart_lines_price_code", "price_code"),
        Index("ix_d2c_cart_lines_product_code", "product_code"),
        Index("ix_d2c_cart_lines_sku_code", "sku_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cart_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_carts.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sku_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    offer_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    offer_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    offer_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    offer_subtitle: Mapped[str | None] = mapped_column(String(240), nullable=True)
    offer_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    price_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    source_offer_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_position_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    product_code: Mapped[str] = mapped_column(String(96), nullable=False)
    sku_code: Mapped[str] = mapped_column(String(128), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pms_item_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    pms_sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    category_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    brand_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    sales_unit_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sales_unit_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(128), nullable=True)
    spec_text: Mapped[str | None] = mapped_column(String(240), nullable=True)
    price_list_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    compare_at_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_sku_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_price_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
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
