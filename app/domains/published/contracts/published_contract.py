"""Runtime published model API contracts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PublishedHealthResponse(BaseModel):
    status: str
    module: str
    storage: str


class PublishedProductContract(BaseModel):
    id: int
    publish_version: str
    pms_item_id: int | None
    pms_sku: str | None
    product_code: str
    product_name: str
    display_name: str
    description: str | None
    image_url: str | None
    category_code: str | None
    category_name: str | None
    brand_code: str | None
    brand_name: str | None
    display_status: str
    sell_status: str
    sort_order: int
    visible_from: datetime | None
    visible_until: datetime | None
    published_at: datetime
    source_product_id: int | None
    source_updated_at: datetime | None
    raw_payload: dict[str, Any] | None


class PublishedProductsResponse(BaseModel):
    count: int = Field(..., ge=0)
    products: list[PublishedProductContract]


class PublishedSkuContract(BaseModel):
    id: int
    publish_version: str
    product_code: str
    sku_code: str
    sku_name: str
    display_sku_name: str
    sales_unit_code: str | None
    sales_unit_name: str | None
    barcode: str | None
    spec_text: str | None
    is_sellable: bool
    sort_order: int
    published_at: datetime
    source_sku_id: int | None
    source_updated_at: datetime | None
    raw_payload: dict[str, Any] | None


class PublishedSkusResponse(BaseModel):
    count: int = Field(..., ge=0)
    skus: list[PublishedSkuContract]


class PublishedPriceContract(BaseModel):
    id: int
    publish_version: str
    price_list_code: str
    channel: str
    sku_code: str
    currency: str
    price_cents: int
    compare_at_price_cents: int | None
    effective_from: datetime | None
    effective_until: datetime | None
    is_active: bool
    priority: int
    published_at: datetime
    source_price_id: int | None
    source_updated_at: datetime | None
    raw_payload: dict[str, Any] | None


class PublishedPricesResponse(BaseModel):
    count: int = Field(..., ge=0)
    prices: list[PublishedPriceContract]


class PublishedPromotionContract(BaseModel):
    id: int
    publish_version: str
    promotion_code: str
    promotion_name: str
    promotion_type: str
    discount_type: str
    discount_value: int
    scope_type: str
    min_order_amount_cents: int | None
    max_discount_cents: int | None
    currency: str
    starts_at: datetime | None
    ends_at: datetime | None
    priority: int
    stackable: bool
    is_active: bool
    published_at: datetime
    source_promotion_id: int | None
    source_updated_at: datetime | None
    raw_payload: dict[str, Any] | None


class PublishedPromotionsResponse(BaseModel):
    count: int = Field(..., ge=0)
    promotions: list[PublishedPromotionContract]


class PublishedCouponContract(BaseModel):
    id: int
    publish_version: str
    coupon_code: str
    coupon_name: str
    promotion_code: str
    coupon_type: str
    total_limit: int | None
    per_customer_limit: int | None
    starts_at: datetime | None
    ends_at: datetime | None
    is_active: bool
    published_at: datetime
    source_coupon_id: int | None
    source_updated_at: datetime | None
    raw_payload: dict[str, Any] | None


class PublishedCouponsResponse(BaseModel):
    count: int = Field(..., ge=0)
    coupons: list[PublishedCouponContract]


class PublishSyncRunContract(BaseModel):
    id: int
    sync_scope: str
    source_service: str
    source_base_url: str | None
    source_endpoint: str | None
    publish_version: str | None
    status: str
    started_at: datetime
    finished_at: datetime | None
    requested_by: str | None
    rows_fetched: int
    rows_upserted: int
    rows_deleted: int
    error_code: str | None
    error_message: str | None
    raw_summary: dict[str, Any] | None


class PublishSyncRunsResponse(BaseModel):
    count: int = Field(..., ge=0)
    sync_runs: list[PublishSyncRunContract]
