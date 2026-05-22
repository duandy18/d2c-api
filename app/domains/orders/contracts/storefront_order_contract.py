"""Storefront order API contracts."""

from datetime import datetime

from pydantic import BaseModel, Field


class OrderCheckoutRequest(BaseModel):
    cart_code: str = Field(..., min_length=1, max_length=96)
    recipient_name: str = Field(..., min_length=1, max_length=128)
    recipient_phone: str = Field(..., min_length=1, max_length=32)
    shipping_country: str = Field(default="US", min_length=1, max_length=64)
    shipping_province: str = Field(..., min_length=1, max_length=64)
    shipping_city: str = Field(..., min_length=1, max_length=64)
    shipping_district: str | None = Field(default=None, max_length=64)
    shipping_address_line1: str = Field(..., min_length=1, max_length=255)
    shipping_address_line2: str | None = Field(default=None, max_length=255)
    shipping_postal_code: str | None = Field(default=None, max_length=32)
    payment_provider: str = Field(default="mock", min_length=1, max_length=32)
    payment_method: str = Field(default="mock", min_length=1, max_length=64)
    coupon_code: str | None = Field(default=None, max_length=64)


class OrderLineResponse(BaseModel):
    product_code: str
    sku_code: str
    product_name: str
    sku_name: str
    quantity: int
    unit_price_cents: int
    line_subtotal_cents: int


class PaymentResponse(BaseModel):
    payment_no: str
    provider: str
    payment_method: str
    status: str
    amount_cents: int
    currency: str
    provider_payment_id: str | None
    provider_trade_no: str | None
    payment_reference: str | None
    paid_at: datetime | None
    created_at: datetime


class OrderResponse(BaseModel):
    order_no: str
    cart_code: str
    status: str
    currency: str
    item_count: int
    subtotal_cents: int
    discount_cents: int
    payable_cents: int
    promotion_code: str | None
    coupon_code: str | None
    recipient_name: str
    recipient_phone: str
    shipping_country: str
    shipping_province: str
    shipping_city: str
    shipping_district: str | None
    shipping_address_line1: str
    shipping_address_line2: str | None
    shipping_postal_code: str | None
    paid_at: datetime | None
    created_at: datetime
    lines: list[OrderLineResponse]
    payment: PaymentResponse | None
