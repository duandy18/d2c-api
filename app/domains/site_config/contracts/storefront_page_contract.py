"""Storefront page route surface contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

StorefrontPagesDataSource = Literal["d2c_storefront_pages"]


class StorefrontPageRoute(BaseModel):
    page_code: str
    page_type: str
    route_path: str
    title: str
    description: str | None = None
    status: str
    auth_required: bool
    navigation_label: str | None = None
    navigation_group: str
    sort_order: int = Field(..., ge=0)


class StorefrontPagesResponse(BaseModel):
    data_source: StorefrontPagesDataSource = "d2c_storefront_pages"
    pages: list[StorefrontPageRoute] = Field(default_factory=list)
    count: int = Field(..., ge=0)
