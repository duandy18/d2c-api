"""Backoffice site configuration contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domains.site_config.contracts.storefront_home_contract import (
    JsonRecord,
    StorefrontHomeOffer,
    StorefrontHomeSlotItem,
    StorefrontSiteSummary,
)


class BackofficeValidationIssue(BaseModel):
    level: Literal["error", "warning"]
    code: str
    message: str
    slot_code: str | None = None
    field_key: str | None = None
    offer_code: str | None = None


class BackofficeSlotOfferPosition(BaseModel):
    position_code: str
    offer_code: str
    position_type: str = "manual"
    is_featured: bool = False
    sort_order: int = Field(..., ge=0)
    is_active: bool = True
    visible_from: datetime | None = None
    visible_until: datetime | None = None
    offer: StorefrontHomeOffer | None = None
    validation_issues: list[BackofficeValidationIssue] = Field(default_factory=list)


class BackofficePageSlot(BaseModel):
    slot_code: str
    slot_type: str
    slot_group: str
    title: str
    subtitle: str | None = None
    content: JsonRecord = Field(default_factory=dict)
    presentation: JsonRecord = Field(default_factory=dict)
    sort_order: int = Field(..., ge=0)
    is_active: bool = True
    supports_items: bool
    supports_offers: bool
    items: list[StorefrontHomeSlotItem] = Field(default_factory=list)
    offer_positions: list[BackofficeSlotOfferPosition] = Field(default_factory=list)


class BackofficeHomePage(BaseModel):
    page_code: str
    page_type: str
    route_path: str
    title: str
    description: str | None = None
    status: str
    seo_title: str | None = None
    seo_description: str | None = None
    slots: list[BackofficePageSlot] = Field(default_factory=list)


class BackofficeHomeConfigResponse(BaseModel):
    site: StorefrontSiteSummary | None = None
    page: BackofficeHomePage | None = None
    validation_issues: list[BackofficeValidationIssue] = Field(default_factory=list)


class BackofficeHomePagePatchRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    description: str | None = None
    status: Literal["active", "disabled"] | None = None
    seo_title: str | None = Field(default=None, max_length=180)
    seo_description: str | None = None


class BackofficeSlotPatchRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    subtitle: str | None = Field(default=None, max_length=240)
    content: JsonRecord | None = None
    presentation: JsonRecord | None = None
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class BackofficeSlotItemPut(BaseModel):
    item_code: str = Field(..., min_length=1, max_length=96)
    item_type: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=160)
    title: str | None = Field(default=None, max_length=160)
    subtitle: str | None = Field(default=None, max_length=240)
    description: str | None = None
    icon: str | None = Field(default=None, max_length=64)
    image_url: str | None = None
    link_type: str | None = Field(default=None, max_length=32)
    link_value: str | None = Field(default=None, max_length=240)
    payload: JsonRecord = Field(default_factory=dict)
    sort_order: int = Field(..., ge=0)
    is_active: bool = True


class BackofficeSlotItemsPutRequest(BaseModel):
    items: list[BackofficeSlotItemPut] = Field(default_factory=list)


class BackofficeSlotOfferPositionPut(BaseModel):
    position_code: str = Field(..., min_length=1, max_length=96)
    offer_code: str = Field(..., min_length=1, max_length=96)
    position_type: str = Field(default="manual", max_length=64)
    is_featured: bool = False
    sort_order: int = Field(..., ge=0)
    is_active: bool = True
    visible_from: datetime | None = None
    visible_until: datetime | None = None


class BackofficeSlotOfferPositionsPutRequest(BaseModel):
    offer_positions: list[BackofficeSlotOfferPositionPut] = Field(default_factory=list)


class BackofficeOfferResolveResponse(BaseModel):
    offer: StorefrontHomeOffer
    raw: dict[str, Any] = Field(default_factory=dict)
