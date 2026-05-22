"""Catalog and pricing domain ORM models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm import Base


class ProductCategory(Base):
    __tablename__ = "d2c_product_categories"
    __table_args__ = (
        UniqueConstraint("code", name="uq_d2c_product_categories_code"),
        Index("ix_d2c_product_categories_code", "code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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


class Unit(Base):
    __tablename__ = "d2c_units"
    __table_args__ = (
        UniqueConstraint("unit_code", name="uq_d2c_units_unit_code"),
        CheckConstraint("precision >= 0", name="ck_d2c_units_precision_non_negative"),
        CheckConstraint(
            "conversion_factor IS NULL OR conversion_factor > 0",
            name="ck_d2c_units_conversion_factor_positive",
        ),
        Index("ix_d2c_units_unit_code", "unit_code"),
        Index("ix_d2c_units_unit_type", "unit_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    unit_code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    precision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    is_base_unit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    base_unit_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    conversion_factor: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    sort_order: Mapped[int] = mapped_column(
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


class Product(Base):
    __tablename__ = "d2c_products"
    __table_args__ = (
        UniqueConstraint("product_code", name="uq_d2c_products_product_code"),
        Index("ix_d2c_products_product_code", "product_code"),
        Index("ix_d2c_products_category_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_code: Mapped[str] = mapped_column(String(96), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(240), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_product_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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


class ProductSku(Base):
    __tablename__ = "d2c_product_skus"
    __table_args__ = (
        UniqueConstraint("sku_code", name="uq_d2c_product_skus_sku_code"),
        CheckConstraint(
            "package_quantity > 0",
            name="ck_d2c_product_skus_package_quantity_positive",
        ),
        Index("ix_d2c_product_skus_sku_code", "sku_code"),
        Index("ix_d2c_product_skus_product_id", "product_id"),
        Index("ix_d2c_product_skus_sales_unit_id", "sales_unit_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_products.id", ondelete="CASCADE"),
        nullable=False,
    )
    sku_code: Mapped[str] = mapped_column(String(96), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    stock_status: Mapped[str] = mapped_column(String(32), nullable=False, default="in_stock")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales_unit_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_units.id", ondelete="RESTRICT"),
        nullable=False,
    )
    package_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    package_unit_text: Mapped[str] = mapped_column(String(64), nullable=False)
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


class PriceList(Base):
    __tablename__ = "d2c_price_lists"
    __table_args__ = (
        UniqueConstraint("price_list_code", name="uq_d2c_price_lists_code"),
        CheckConstraint(
            "priority >= 0",
            name="ck_d2c_price_lists_priority_non_negative",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from",
            name="ck_d2c_price_lists_effective_range_valid",
        ),
        Index("ix_d2c_price_lists_channel", "channel"),
        Index("ix_d2c_price_lists_currency", "currency"),
        Index("ix_d2c_price_lists_is_default", "is_default"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    price_list_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    region_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="US",
        server_default="US",
    )
    channel: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="storefront",
        server_default="storefront",
    )
    customer_segment: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="default",
        server_default="default",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default="100",
    )
    is_default: Mapped[bool] = mapped_column(
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
    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    effective_to: Mapped[datetime | None] = mapped_column(
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


class SkuPrice(Base):
    __tablename__ = "d2c_sku_prices"
    __table_args__ = (
        UniqueConstraint(
            "price_list_id",
            "sku_id",
            name="uq_d2c_sku_prices_price_list_id_sku_id",
        ),
        CheckConstraint(
            "price_cents >= 0",
            name="ck_d2c_sku_prices_price_cents_non_negative",
        ),
        CheckConstraint(
            "compare_at_price_cents IS NULL OR compare_at_price_cents >= price_cents",
            name="ck_d2c_sku_prices_compare_at_price_valid",
        ),
        CheckConstraint(
            "effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from",
            name="ck_d2c_sku_prices_effective_range_valid",
        ),
        Index("ix_d2c_sku_prices_is_active", "is_active"),
        Index("ix_d2c_sku_prices_price_list_id", "price_list_id"),
        Index("ix_d2c_sku_prices_sku_id", "sku_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    price_list_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_price_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    sku_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_product_skus.id", ondelete="CASCADE"),
        nullable=False,
    )
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    compare_at_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
