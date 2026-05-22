from typing import Literal

from pydantic import BaseModel, Field

CatalogDataSource = Literal["placeholder_static_catalog"]
CatalogProductStatus = Literal["active", "inactive"]
CatalogStockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class CatalogProduct(BaseModel):
    product_id: str = Field(..., description="Stable D2C catalog product identifier.")
    sku: str = Field(..., description="Display SKU for the placeholder product.")
    name: str = Field(..., description="Product display name.")
    category: str = Field(..., description="First-level storefront category.")
    description: str = Field(..., description="Short storefront description.")
    price_cents: int = Field(..., ge=0, description="Display price in cents.")
    currency: str = Field(default="USD", description="Display currency.")
    tags: list[str] = Field(default_factory=list, description="Storefront tags.")
    status: CatalogProductStatus = Field(default="active", description="Catalog status.")
    stock_status: CatalogStockStatus = Field(default="in_stock")
    image_url: str | None = Field(default=None, description="Optional product image URL.")


class CatalogProductsResponse(BaseModel):
    data_source: CatalogDataSource = Field(
        default="placeholder_static_catalog",
        description="Current data source. Future target is PMS projection.",
    )
    count: int = Field(..., ge=0, description="Number of returned products.")
    products: list[CatalogProduct]
