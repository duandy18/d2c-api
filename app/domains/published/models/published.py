"""Runtime published model tables.

These tables are the customer-facing runtime read model. They are populated
from d2c-backoffice-api published exports in a later sync step.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm import Base


class PublishedProduct(Base):
    __tablename__ = "d2c_published_products"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "product_code",
            name="uq_d2c_published_products_version_product",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_d2c_published_products_sort_order_non_negative",
        ),
        CheckConstraint(
            "visible_until IS NULL OR visible_from IS NULL OR visible_until > visible_from",
            name="ck_d2c_published_products_visible_range_valid",
        ),
        Index("ix_d2c_published_products_product_code", "product_code"),
        Index(
            "ix_d2c_published_products_version_visibility",
            "publish_version",
            "display_status",
            "sell_status",
        ),
        Index("ix_d2c_published_products_category", "category_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pms_item_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    pms_sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    product_code: Mapped[str] = mapped_column(String(96), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    category_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    brand_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    display_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="hidden",
        server_default="hidden",
    )
    sell_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="not_sellable",
        server_default="not_sellable",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )
    visible_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    visible_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source_product_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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


class PublishedSku(Base):
    __tablename__ = "d2c_published_skus"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "sku_code",
            name="uq_d2c_published_skus_version_sku",
        ),
        CheckConstraint(
            "sort_order >= 0",
            name="ck_d2c_published_skus_sort_order_non_negative",
        ),
        ForeignKeyConstraint(
            ["publish_version", "product_code"],
            ["d2c_published_products.publish_version", "d2c_published_products.product_code"],
            name="fk_d2c_published_skus_product_version",
            ondelete="CASCADE",
        ),
        Index("ix_d2c_published_skus_product_code", "product_code"),
        Index("ix_d2c_published_skus_sku_code", "sku_code"),
        Index("ix_d2c_published_skus_version_sellable", "publish_version", "is_sellable"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    product_code: Mapped[str] = mapped_column(String(96), nullable=False)
    sku_code: Mapped[str] = mapped_column(String(128), nullable=False)
    sku_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_sku_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sales_unit_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sales_unit_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(128), nullable=True)
    spec_text: Mapped[str | None] = mapped_column(String(240), nullable=True)
    is_sellable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source_sku_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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


class PublishedPrice(Base):
    __tablename__ = "d2c_published_prices"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "price_list_code",
            "channel",
            "sku_code",
            name="uq_d2c_published_prices_version_list_channel_sku",
        ),
        CheckConstraint("price_cents >= 0", name="ck_d2c_published_prices_price_non_negative"),
        CheckConstraint("priority >= 0", name="ck_d2c_published_prices_priority_non_negative"),
        CheckConstraint(
            "compare_at_price_cents IS NULL OR compare_at_price_cents >= price_cents",
            name="ck_d2c_published_prices_compare_at_valid",
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL OR effective_until > effective_from",
            name="ck_d2c_published_prices_effective_range_valid",
        ),
        ForeignKeyConstraint(
            ["publish_version", "sku_code"],
            ["d2c_published_skus.publish_version", "d2c_published_skus.sku_code"],
            name="fk_d2c_published_prices_sku_version",
            ondelete="CASCADE",
        ),
        Index(
            "ix_d2c_published_prices_sku_channel_active",
            "sku_code",
            "channel",
            "is_active",
        ),
        Index("ix_d2c_published_prices_version_priority", "publish_version", "priority"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    price_list_code: Mapped[str] = mapped_column(String(96), nullable=False)
    channel: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="storefront",
        server_default="storefront",
    )
    sku_code: Mapped[str] = mapped_column(String(128), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    compare_at_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source_price_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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


class PublishedPromotion(Base):
    __tablename__ = "d2c_published_promotions"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "promotion_code",
            name="uq_d2c_published_promotions_version_code",
        ),
        CheckConstraint(
            "discount_value > 0",
            name="ck_d2c_published_promotions_discount_positive",
        ),
        CheckConstraint(
            "discount_type <> 'percentage' OR discount_value <= 100",
            name="ck_d2c_published_promotions_percentage_valid",
        ),
        CheckConstraint(
            "min_order_amount_cents IS NULL OR min_order_amount_cents >= 0",
            name="ck_d2c_published_promotions_min_order_non_negative",
        ),
        CheckConstraint(
            "max_discount_cents IS NULL OR max_discount_cents >= 0",
            name="ck_d2c_published_promotions_max_discount_non_negative",
        ),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_published_promotions_effective_range_valid",
        ),
        CheckConstraint(
            "priority >= 0",
            name="ck_d2c_published_promotions_priority_non_negative",
        ),
        Index("ix_d2c_published_promotions_code", "promotion_code"),
        Index(
            "ix_d2c_published_promotions_runtime",
            "publish_version",
            "is_active",
            "starts_at",
            "ends_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_code: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_name: Mapped[str] = mapped_column(String(160), nullable=False)
    promotion_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    min_order_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_discount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100"
    )
    stackable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source_promotion_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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


class PublishedCoupon(Base):
    __tablename__ = "d2c_published_coupons"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "coupon_code",
            name="uq_d2c_published_coupons_version_code",
        ),
        CheckConstraint(
            "total_limit IS NULL OR total_limit > 0",
            name="ck_d2c_published_coupons_total_limit_positive",
        ),
        CheckConstraint(
            "per_customer_limit IS NULL OR per_customer_limit > 0",
            name="ck_d2c_published_coupons_per_customer_limit_positive",
        ),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_d2c_published_coupons_effective_range_valid",
        ),
        ForeignKeyConstraint(
            ["publish_version", "promotion_code"],
            [
                "d2c_published_promotions.publish_version",
                "d2c_published_promotions.promotion_code",
            ],
            name="fk_d2c_published_coupons_promotion_version",
            ondelete="CASCADE",
        ),
        Index("ix_d2c_published_coupons_code", "coupon_code"),
        Index(
            "ix_d2c_published_coupons_runtime",
            "publish_version",
            "is_active",
            "starts_at",
            "ends_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    coupon_code: Mapped[str] = mapped_column(String(64), nullable=False)
    coupon_name: Mapped[str] = mapped_column(String(160), nullable=False)
    promotion_code: Mapped[str] = mapped_column(String(64), nullable=False)
    coupon_type: Mapped[str] = mapped_column(String(32), nullable=False)
    total_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_customer_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    source_coupon_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
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


class PublishSyncRun(Base):
    __tablename__ = "d2c_publish_sync_runs"
    __table_args__ = (
        CheckConstraint(
            "rows_fetched >= 0",
            name="ck_d2c_publish_sync_runs_rows_fetched_non_negative",
        ),
        CheckConstraint(
            "rows_upserted >= 0",
            name="ck_d2c_publish_sync_runs_rows_upserted_non_negative",
        ),
        CheckConstraint(
            "rows_deleted >= 0",
            name="ck_d2c_publish_sync_runs_rows_deleted_non_negative",
        ),
        Index("ix_d2c_publish_sync_runs_scope_status", "sync_scope", "status"),
        Index("ix_d2c_publish_sync_runs_publish_version", "publish_version"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sync_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    source_service: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="d2c-backoffice-api",
        server_default="d2c-backoffice-api",
    )
    source_base_url: Mapped[str | None] = mapped_column(String(240), nullable=True)
    source_endpoint: Mapped[str | None] = mapped_column(String(240), nullable=True)
    publish_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rows_fetched: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    rows_upserted: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    rows_deleted: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
