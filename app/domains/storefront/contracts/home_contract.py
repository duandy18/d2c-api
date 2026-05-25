"""Storefront home API contracts.

This is the terminal customer-facing client presentation contract. The frontend
renders Page / Region / Block / Position / Offer protocol from this endpoint
instead of rebuilding storefront layout itself.
"""

from typing import Literal

from pydantic import BaseModel, Field

StorefrontHomeDataSource = Literal["d2c_published_client_presentation_snapshot"]
StorefrontStockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class StorefrontHomeBlockLayout(BaseModel):
    display_type: str
    columns_desktop: int = Field(..., ge=1)
    columns_tablet: int = Field(..., ge=1)
    columns_mobile: int = Field(..., ge=1)
    card_size: str
    image_ratio: str
    show_promotion_badge: bool
    show_sales_summary: bool
    show_review_summary: bool
    show_compare_price: bool
    show_quantity_stepper: bool
    max_items: int | None = Field(default=None, ge=1)


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


class StorefrontHomeBlockPosition(BaseModel):
    position_code: str
    offer_code: str
    sort_order: int
    position_type: str
    is_featured: bool
    offer: StorefrontHomeOffer


class StorefrontHomeBlock(BaseModel):
    block_code: str
    block_type: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    sort_order: int
    layout: StorefrontHomeBlockLayout
    data_binding_codes: list[str] = Field(default_factory=list)
    visibility_rule_codes: list[str] = Field(default_factory=list)
    action_policy_codes: list[str] = Field(default_factory=list)
    tracking_policy_codes: list[str] = Field(default_factory=list)
    positions: list[StorefrontHomeBlockPosition] = Field(default_factory=list)


class StorefrontHomeRegion(BaseModel):
    region_code: str
    region_type: str
    title: str
    description: str | None = None
    sort_order: int
    allowed_block_types: list[str] = Field(default_factory=list)
    blocks: list[StorefrontHomeBlock] = Field(default_factory=list)


class StorefrontHomePage(BaseModel):
    page_code: str
    page_type: str
    route_path: str
    title: str
    description: str | None = None
    regions: list[StorefrontHomeRegion] = Field(default_factory=list)


class StorefrontHomeResponse(BaseModel):
    data_source: StorefrontHomeDataSource = "d2c_published_client_presentation_snapshot"
    publish_version: str | None
    page_code: str | None = None
    surface_code: str = "web_desktop"
    region_count: int = Field(..., ge=0)
    block_count: int = Field(..., ge=0)
    offer_count: int = Field(..., ge=0)
    page: StorefrontHomePage | None = None
