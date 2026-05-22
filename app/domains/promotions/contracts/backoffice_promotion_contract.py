"""Backoffice promotion API contracts."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PromotionType = Literal["store_campaign"]
DiscountType = Literal["percentage"]
ScopeType = Literal["all_store"]


class BackofficePromotionHealthResponse(BaseModel):
    status: str
    module: str
    surface: str


class BackofficePromotionCreateRequest(BaseModel):
    promotion_code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=160)
    description: str | None = Field(default=None)
    promotion_type: PromotionType = Field(default="store_campaign")
    discount_type: DiscountType = Field(default="percentage")
    discount_value: int = Field(..., ge=1, le=100)
    scope_type: ScopeType = Field(default="all_store")
    min_order_amount_cents: int | None = Field(default=None, ge=0)
    max_discount_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    priority: int = Field(default=100, ge=0)
    stackable: bool = Field(default=False)


class BackofficePromotion(BaseModel):
    id: int
    promotion_code: str
    name: str
    description: str | None
    promotion_type: str
    discount_type: str
    discount_value: int
    scope_type: str
    min_order_amount_cents: int | None
    max_discount_cents: int | None
    currency: str
    starts_at: datetime | None
    ends_at: datetime | None
    status: str
    priority: int
    stackable: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BackofficePromotionsResponse(BaseModel):
    count: int = Field(..., ge=0)
    promotions: list[BackofficePromotion]


class BackofficePromotionTarget(BaseModel):
    id: int
    promotion_id: int
    promotion_code: str
    target_type: str
    target_id: int | None
    target_code: str | None
    created_at: datetime


class BackofficePromotionTargetsResponse(BaseModel):
    count: int = Field(..., ge=0)
    promotion_targets: list[BackofficePromotionTarget]


class BackofficeCoupon(BaseModel):
    id: int
    coupon_code: str
    name: str
    promotion_id: int
    promotion_code: str
    coupon_type: str
    total_limit: int | None
    per_customer_limit: int | None
    starts_at: datetime | None
    ends_at: datetime | None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BackofficeCouponsResponse(BaseModel):
    count: int = Field(..., ge=0)
    coupons: list[BackofficeCoupon]


class BackofficeCustomerCoupon(BaseModel):
    id: int
    customer_coupon_code: str
    coupon_id: int
    coupon_code: str
    promotion_id: int
    promotion_code: str
    customer_id: int
    status: str
    claimed_at: datetime | None
    used_at: datetime | None
    order_id: int | None
    created_at: datetime
    updated_at: datetime


class BackofficeCustomerCouponsResponse(BaseModel):
    count: int = Field(..., ge=0)
    customer_coupons: list[BackofficeCustomerCoupon]
