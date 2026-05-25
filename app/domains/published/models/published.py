"""Runtime published model tables.

These tables are the customer-facing runtime read model. They are populated
from d2c-backoffice-api published exports in a later sync step.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
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
        Index("ix_d2c_published_coupons_code", "coupon_code"),
        Index(
            "ix_d2c_published_coupons_runtime",
            "publish_version",
            "is_active",
            "starts_at",
            "ends_at",
        ),
        Index("ix_d2c_pub_coupons_rule", "publish_version", "promotion_code"),
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


class PublishedStorefrontSection(Base):
    __tablename__ = "d2c_published_storefront_sections"
    __table_args__ = (
        UniqueConstraint("publish_version", "section_code", name="uq_d2c_pub_sections_code"),
        Index("ix_d2c_pub_sections_group_sort", "publish_version", "group_code", "sort_order"),
        Index("ix_d2c_pub_sections_status", "publish_version", "display_status", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    section_code: Mapped[str] = mapped_column(String(96), nullable=False)
    section_type: Mapped[str] = mapped_column(String(32), nullable=False)
    group_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(240), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    display_status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_section_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PublishedStorefrontSectionLayout(Base):
    __tablename__ = "d2c_published_storefront_section_layouts"
    __table_args__ = (
        UniqueConstraint("publish_version", "section_code", name="uq_d2c_pub_section_layouts_code"),
        Index("ix_d2c_pub_section_layouts_display", "publish_version", "display_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    section_code: Mapped[str] = mapped_column(String(96), nullable=False)
    display_type: Mapped[str] = mapped_column(String(32), nullable=False)
    columns_desktop: Mapped[int] = mapped_column(Integer, nullable=False)
    columns_tablet: Mapped[int] = mapped_column(Integer, nullable=False)
    columns_mobile: Mapped[int] = mapped_column(Integer, nullable=False)
    card_size: Mapped[str] = mapped_column(String(32), nullable=False)
    image_ratio: Mapped[str] = mapped_column(String(16), nullable=False)
    show_promotion_badge: Mapped[bool] = mapped_column(Boolean, nullable=False)
    show_sales_summary: Mapped[bool] = mapped_column(Boolean, nullable=False)
    show_review_summary: Mapped[bool] = mapped_column(Boolean, nullable=False)
    show_compare_price: Mapped[bool] = mapped_column(Boolean, nullable=False)
    show_quantity_stepper: Mapped[bool] = mapped_column(Boolean, nullable=False)
    max_items: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_layout_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )



class PublishedStorefrontSectionPosition(Base):
    __tablename__ = "d2c_published_storefront_section_positions"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "position_code",
            name="uq_d2c_pub_sec_pos_code",
        ),
        Index("ix_d2c_pub_sec_pos_section", "publish_version", "section_code", "sort_order"),
        Index("ix_d2c_pub_sec_pos_offer", "publish_version", "offer_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    section_code: Mapped[str] = mapped_column(String(96), nullable=False)
    position_code: Mapped[str] = mapped_column(String(120), nullable=False)
    offer_code: Mapped[str] = mapped_column(String(96), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    position_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False)
    visible_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    visible_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_position_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

class PublishedGroup(Base):
    __tablename__ = "d2c_published_groups"
    __table_args__ = (
        UniqueConstraint("publish_version", "group_code", name="uq_d2c_pub_groups_code"),
        Index("ix_d2c_pub_groups_version_sort", "publish_version", "sort_order"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    group_code: Mapped[str] = mapped_column(String(96), nullable=False)
    group_name: Mapped[str] = mapped_column(String(160), nullable=False)
    group_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    display_status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PublishedOffer(Base):
    __tablename__ = "d2c_published_offers"
    __table_args__ = (
        UniqueConstraint("publish_version", "offer_code", name="uq_d2c_pub_offers_code"),
        Index("ix_d2c_pub_offers_version_type", "publish_version", "offer_type"),
        Index("ix_d2c_pub_offers_sellable", "publish_version", "display_status", "sell_status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    offer_code: Mapped[str] = mapped_column(String(96), nullable=False)
    offer_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(240), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_status: Mapped[str] = mapped_column(String(32), nullable=False)
    sell_status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_offer_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PublishedOfferComponent(Base):
    __tablename__ = "d2c_published_offer_components"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "offer_code",
            "component_no",
            name="uq_d2c_pub_components_no",
        ),
        Index("ix_d2c_pub_components_offer", "publish_version", "offer_code"),
        Index("ix_d2c_pub_components_pms_item", "pms_item_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    offer_code: Mapped[str] = mapped_column(String(96), nullable=False)
    component_no: Mapped[int] = mapped_column(Integer, nullable=False)
    pms_item_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    pms_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    pms_sku_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sku_code: Mapped[str] = mapped_column(String(128), nullable=False)
    pms_item_uom_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uom_code: Mapped[str] = mapped_column(String(32), nullable=False)
    uom_name: Mapped[str] = mapped_column(String(80), nullable=False)
    pms_barcode_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    component_role: Mapped[str] = mapped_column(String(32), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_component_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PublishedOfferPrice(Base):
    __tablename__ = "d2c_published_offer_prices"
    __table_args__ = (
        UniqueConstraint("publish_version", "price_code", name="uq_d2c_pub_prices_code"),
        Index("ix_d2c_pub_prices_offer", "publish_version", "offer_code", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    offer_code: Mapped[str] = mapped_column(String(96), nullable=False)
    price_code: Mapped[str] = mapped_column(String(96), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    compare_at_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    source_price_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PublishedOfferPosition(Base):
    __tablename__ = "d2c_published_offer_positions"
    __table_args__ = (
        UniqueConstraint("publish_version", "position_code", name="uq_d2c_pub_positions_code"),
        Index("ix_d2c_pub_positions_group", "publish_version", "group_code", "sort_order"),
        Index("ix_d2c_pub_positions_offer", "publish_version", "offer_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    position_code: Mapped[str] = mapped_column(String(120), nullable=False)
    group_code: Mapped[str] = mapped_column(String(96), nullable=False)
    offer_code: Mapped[str] = mapped_column(String(96), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    position_source: Mapped[str] = mapped_column(String(32), nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False)
    visible_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    visible_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_position_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PublishedPromotionRule(Base):
    __tablename__ = "d2c_published_promotion_rules"
    __table_args__ = (
        UniqueConstraint("publish_version", "promotion_code", name="uq_d2c_pub_rules_code"),
        Index("ix_d2c_pub_rules_active", "publish_version", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_code: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    promotion_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(32), nullable=False)
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    threshold_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_discount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    stackable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    display_badge: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_promotion_rule_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PublishedPromotionTarget(Base):
    __tablename__ = "d2c_published_promotion_targets"
    __table_args__ = (
        UniqueConstraint(
            "publish_version",
            "promotion_code",
            "target_type",
            "target_code",
            "target_id",
            name="uq_d2c_pub_targets_scope",
        ),
        Index("ix_d2c_pub_targets_rule", "publish_version", "promotion_code"),
        Index("ix_d2c_pub_targets_target", "publish_version", "target_type", "target_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    publish_version: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_code: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_code: Mapped[str | None] = mapped_column(String(96), nullable=True)
    source_target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
