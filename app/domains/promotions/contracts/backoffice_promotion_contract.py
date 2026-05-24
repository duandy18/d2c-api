"""Backoffice promotion usage API contracts retained in d2c-api."""

from datetime import datetime

from pydantic import BaseModel, Field


class BackofficeCustomerCoupon(BaseModel):
    id: int
    customer_coupon_code: str
    publish_version: str | None
    coupon_code: str | None
    coupon_name: str | None
    coupon_type: str | None
    promotion_code: str | None
    promotion_name: str | None
    promotion_type: str | None
    promotion_discount_type: str | None
    promotion_discount_value: int | None
    customer_id: int
    status: str
    claimed_at: datetime | None
    used_at: datetime | None
    order_id: int | None
    order_no: str | None
    created_at: datetime
    updated_at: datetime


class BackofficeCustomerCouponsResponse(BaseModel):
    count: int = Field(..., ge=0)
    customer_coupons: list[BackofficeCustomerCoupon]
