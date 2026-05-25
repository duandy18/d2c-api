"""Storefront catalog API contracts.

HTTP paths remain /catalog/* for storefront stability, but the runtime source is
the terminal published Offer / Group / Position / Price snapshot model.
"""

from typing import Literal

from pydantic import BaseModel, Field

CatalogDataSource = Literal["d2c_published_offer_snapshot"]
CatalogProductStatus = Literal["active", "inactive"]
CatalogStockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class CatalogCategory(BaseModel):
    code: str = Field(..., description="Storefront group code.")
    name: str = Field(..., description="Storefront group name.")
    sort_order: int = Field(..., description="Display sort order.")


class CatalogCategoriesResponse(BaseModel):
    data_source: CatalogDataSource = Field(default="d2c_published_offer_snapshot")
    count: int = Field(..., ge=0)
    categories: list[CatalogCategory]


class CatalogProduct(BaseModel):
    product_id: str = Field(..., description="Stable storefront Offer identifier.")
    sku: str = Field(..., description="Display SKU placeholder; currently mirrors offer code.")
    name: str = Field(..., description="Offer display title.")
    category: str = Field(..., description="Primary storefront group name.")
    description: str = Field(..., description="Offer storefront description.")
    price_cents: int = Field(..., ge=0, description="Display price in cents.")
    currency: str = Field(default="USD", description="Display currency.")
    tags: list[str] = Field(default_factory=list, description="Storefront tags.")
    status: CatalogProductStatus = Field(default="active", description="Catalog status.")
    stock_status: CatalogStockStatus = Field(default="in_stock")
    image_url: str | None = Field(default=None, description="Optional offer image URL.")


class CatalogProductsResponse(BaseModel):
    data_source: CatalogDataSource = Field(
        default="d2c_published_offer_snapshot",
        description="Current data source.",
    )
    count: int = Field(..., ge=0, description="Number of returned offers.")
    products: list[CatalogProduct]
