"""Storefront site configuration owner tables."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
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
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.orm import Base


class StorefrontSite(Base):
    __tablename__ = "d2c_storefront_sites"
    __table_args__ = (
        UniqueConstraint("site_code", name="uq_d2c_sf_sites_code"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_d2c_sf_sites_status"),
        Index("ix_d2c_sf_sites_status", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    site_code: Mapped[str] = mapped_column(String(64), nullable=False)
    site_name: Mapped[str] = mapped_column(String(160), nullable=False)
    brand_name: Mapped[str] = mapped_column(String(160), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="active")
    default_currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StorefrontThemeSetting(Base):
    __tablename__ = "d2c_storefront_theme_settings"
    __table_args__ = (
        UniqueConstraint("site_id", "theme_code", name="uq_d2c_sf_theme_code"),
        Index("ix_d2c_sf_theme_active", "site_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    site_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_storefront_sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    theme_code: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_color: Mapped[str] = mapped_column(String(32), nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(32), nullable=False)
    background_color: Mapped[str] = mapped_column(String(32), nullable=False)
    text_color: Mapped[str] = mapped_column(String(32), nullable=False)
    font_family: Mapped[str | None] = mapped_column(String(160), nullable=True)
    corner_radius: Mapped[str] = mapped_column(String(32), nullable=False, server_default="24px")
    button_style: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pill")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StorefrontPage(Base):
    __tablename__ = "d2c_storefront_pages"
    __table_args__ = (
        UniqueConstraint("site_id", "page_code", name="uq_d2c_sf_pages_code"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_d2c_sf_pages_status"),
        CheckConstraint("route_path LIKE '/%'", name="ck_d2c_sf_pages_route_abs"),
        Index("ix_d2c_sf_pages_status", "site_id", "status"),
        Index("ix_d2c_sf_pages_route", "site_id", "route_path"),
        Index("ix_d2c_sf_pages_nav", "site_id", "navigation_group", "sort_order"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    site_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_storefront_sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_code: Mapped[str] = mapped_column(String(64), nullable=False)
    page_type: Mapped[str] = mapped_column(String(32), nullable=False)
    route_path: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="active")
    auth_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    navigation_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    navigation_group: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="main",
        server_default=text("'main'"),
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    seo_title: Mapped[str | None] = mapped_column(String(180), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StorefrontPageSlot(Base):
    __tablename__ = "d2c_storefront_page_slots"
    __table_args__ = (
        UniqueConstraint("page_id", "slot_code", name="uq_d2c_sf_slots_code"),
        CheckConstraint("sort_order >= 0", name="ck_d2c_sf_slots_sort_nonneg"),
        Index("ix_d2c_sf_slots_order", "page_id", "sort_order", "slot_code"),
        Index("ix_d2c_sf_slots_active", "page_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    page_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_storefront_pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_code: Mapped[str] = mapped_column(String(96), nullable=False)
    slot_type: Mapped[str] = mapped_column(String(64), nullable=False)
    slot_group: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(240), nullable=True)
    content_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, server_default=text("'{}'::json")
    )
    presentation_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, server_default=text("'{}'::json")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StorefrontSlotItem(Base):
    __tablename__ = "d2c_storefront_slot_items"
    __table_args__ = (
        UniqueConstraint("slot_id", "item_code", name="uq_d2c_sf_slot_items_code"),
        CheckConstraint("sort_order >= 0", name="ck_d2c_sf_slot_items_sort_nonneg"),
        Index("ix_d2c_sf_slot_items_order", "slot_id", "sort_order", "item_code"),
        Index("ix_d2c_sf_slot_items_active", "slot_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slot_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_storefront_page_slots.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_code: Mapped[str] = mapped_column(String(96), nullable=False)
    item_type: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    subtitle: Mapped[str | None] = mapped_column(String(240), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    link_value: Mapped[str | None] = mapped_column(String(240), nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, server_default=text("'{}'::json")
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StorefrontSlotOfferPosition(Base):
    __tablename__ = "d2c_storefront_slot_offer_positions"
    __table_args__ = (
        UniqueConstraint("slot_id", "position_code", name="uq_d2c_sf_slot_offer_pos_code"),
        UniqueConstraint("slot_id", "offer_code", name="uq_d2c_sf_slot_offer_pos_offer"),
        CheckConstraint("sort_order >= 0", name="ck_d2c_sf_slot_offer_pos_sort_nonneg"),
        CheckConstraint(
            "visible_until IS NULL OR visible_from IS NULL OR visible_until > visible_from",
            name="ck_d2c_sf_slot_offer_pos_window",
        ),
        Index("ix_d2c_sf_slot_offer_pos_order", "slot_id", "sort_order", "position_code"),
        Index("ix_d2c_sf_slot_offer_pos_offer", "offer_code"),
        Index("ix_d2c_sf_slot_offer_pos_active", "slot_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slot_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("d2c_storefront_page_slots.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_code: Mapped[str] = mapped_column(String(96), nullable=False)
    offer_code: Mapped[str] = mapped_column(String(96), nullable=False)
    position_type: Mapped[str] = mapped_column(String(64), nullable=False, server_default="manual")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    visible_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    visible_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

class OfferDisplayMetric(Base):
    """Merchant-maintained display-only metrics for customer-facing offer cards.

    These numbers are not order facts and are not warehouse stock. They are
    storefront presentation data maintained from the backoffice.
    """

    __tablename__ = "d2c_offer_display_metrics"
    __table_args__ = (
        UniqueConstraint("offer_code", name="uq_d2c_offer_disp_metrics_offer"),
        CheckConstraint(
            "display_sold_quantity >= 0",
            name="ck_d2c_offer_disp_sold_non_negative",
        ),
        CheckConstraint(
            "display_paid_customer_count >= 0",
            name="ck_d2c_offer_disp_paid_non_negative",
        ),
        CheckConstraint(
            "display_stock_quantity >= 0",
            name="ck_d2c_offer_disp_stock_non_negative",
        ),
        Index("ix_d2c_offer_disp_metrics_offer", "offer_code"),
        Index("ix_d2c_offer_disp_metrics_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    offer_code: Mapped[str] = mapped_column(String(96), nullable=False)
    display_sold_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    display_paid_customer_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    display_stock_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
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
