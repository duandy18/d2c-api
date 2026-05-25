"""Storefront cart API contracts."""

from pydantic import BaseModel, Field


class CartIdentityRequest(BaseModel):
    anonymous_id: str = Field(..., min_length=8, max_length=96)
    session_code: str = Field(..., min_length=8, max_length=96)


class CartItemUpsertRequest(CartIdentityRequest):
    offer_code: str = Field(..., min_length=1, max_length=96)
    quantity: int = Field(..., ge=0, le=999)


class CartLineResponse(BaseModel):
    offer_code: str
    name: str
    quantity: int
    unit_price_cents: int
    currency: str
    line_subtotal_cents: int


class CartResponse(BaseModel):
    cart_code: str
    anonymous_id: str | None
    session_code: str | None
    currency: str
    line_count: int
    item_count: int
    subtotal_cents: int
    lines: list[CartLineResponse]
