"""Storefront home Slot-first API contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

JsonRecord = dict[str, Any]
StorefrontHomeDataSource = Literal["d2c_storefront_site_config"]
StorefrontStockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class StorefrontTheme(BaseModel):
    theme_code: str
    primary_color: str
    secondary_color: str
    background_color: str
    text_color: str
    font_family: str | None = None
    corner_radius: str
    button_style: str


class StorefrontSiteSummary(BaseModel):
    site_code: str
    site_name: str
    brand_name: str
    logo_url: str | None = None
    default_currency: str
    theme: StorefrontTheme | None = None


class StorefrontHomeOffer(BaseModel):
    offer_code: str
    offer_type: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    image_url: str | None = None

    price_code: str
    price_cents: int = Field(..., ge=0)
    compare_at_price_cents: int | None = None
    currency: str

    promotion_badge: str | None = None
    sold_quantity: int | None = None
    paid_customer_count: int | None = None
    rating_score: float | None = None
    review_count: int | None = None
    review_summary: str | None = None

    tags: list[str] = Field(default_factory=list)
    stock_status: StorefrontStockStatus = "in_stock"
    sell_status: str


class StorefrontHomeOfferPosition(BaseModel):
    position_code: str
    offer_code: str
    position_type: str
    is_featured: bool
    sort_order: int
    offer: StorefrontHomeOffer


class StorefrontHomeSlotItem(BaseModel):
    item_code: str
    item_type: str
    label: str
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    icon: str | None = None
    image_url: str | None = None
    link_type: str | None = None
    link_value: str | None = None
    payload: JsonRecord = Field(default_factory=dict)
    sort_order: int


class StorefrontHomeSlot(BaseModel):
    slot_code: str
    slot_type: str
    slot_group: str
    title: str
    subtitle: str | None = None
    content: JsonRecord = Field(default_factory=dict)
    presentation: JsonRecord = Field(default_factory=dict)
    sort_order: int
    items: list[StorefrontHomeSlotItem] = Field(default_factory=list)
    offers: list[StorefrontHomeOfferPosition] = Field(default_factory=list)


class StorefrontHomePage(BaseModel):
    page_code: str
    page_type: str
    route_path: str
    title: str
    description: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    slots: list[StorefrontHomeSlot] = Field(default_factory=list)


class StorefrontHomeResponse(BaseModel):
    data_source: StorefrontHomeDataSource = "d2c_storefront_site_config"
    site: StorefrontSiteSummary | None = None
    page: StorefrontHomePage | None = None
    slot_count: int = Field(..., ge=0)
    item_count: int = Field(..., ge=0)
    offer_count: int = Field(..., ge=0)
