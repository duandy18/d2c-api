"""Backoffice promotion usage API contracts retained in d2c-api."""

from datetime import datetime

from pydantic import BaseModel, Field


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
