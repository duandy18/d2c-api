"""Runtime published model API contracts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PublishedHealthResponse(BaseModel):
    status: str
    module: str
    storage: str


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
