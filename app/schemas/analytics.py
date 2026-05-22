from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

BehaviorEventType = Literal[
    "page_view",
    "product_view",
    "product_view_duration",
    "product_impression",
    "product_click",
    "add_to_cart",
    "cart_view",
    "checkout_start",
    "checkout_abandon",
    "order_submit",
    "purchase_success",
]


class BehaviorEventRequest(BaseModel):
    anonymous_id: str = Field(..., min_length=8, max_length=96)
    session_code: str = Field(..., min_length=8, max_length=96)
    event_type: BehaviorEventType
    page_path: str = Field(..., min_length=1, max_length=500)
    product_code: str | None = Field(default=None, max_length=96)
    sku_code: str | None = Field(default=None, max_length=96)
    duration_ms: int | None = Field(default=None, ge=0)
    metadata: dict[str, object] | None = None
    occurred_at: datetime | None = None
    referrer: str | None = Field(default=None, max_length=1000)
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=120)


class BehaviorEventResponse(BaseModel):
    accepted: bool = True
    event_code: str
    session_code: str
    event_type: str
    occurred_at: datetime
