"""Storefront home API contracts.

This is the terminal customer-facing home contract. It is intentionally separate
from the older /catalog list contract. The frontend should render Group /
Position / Offer layout from this endpoint instead of rebuilding layout itself.
"""

from typing import Literal

from pydantic import BaseModel, Field

StorefrontHomeDataSource = Literal["d2c_published_storefront_snapshot"]
StorefrontDisplayStyle = Literal["grid", "list", "ranking", "banner"]
StorefrontStockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class StorefrontHomeGroup(BaseModel):
    group_code: str
    group_name: str
    group_kind: str
    description: str | None = None
    image_url: str | None = None
    sort_order: int


class StorefrontHomeOfferCard(BaseModel):
    offer_code: str
    offer_type: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    image_url: str | None = None

    group_code: str
    group_name: str
    position_code: str
    position_sort_order: int
    is_featured: bool

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


class StorefrontHomeSection(BaseModel):
    section_code: str
    group_code: str
    group_name: str
    title: str
    display_style: StorefrontDisplayStyle
    sort_order: int
    offers: list[StorefrontHomeOfferCard]


class StorefrontHomeResponse(BaseModel):
    data_source: StorefrontHomeDataSource = "d2c_published_storefront_snapshot"
    publish_version: str | None
    group_count: int = Field(..., ge=0)
    section_count: int = Field(..., ge=0)
    offer_count: int = Field(..., ge=0)
    groups: list[StorefrontHomeGroup]
    sections: list[StorefrontHomeSection]
