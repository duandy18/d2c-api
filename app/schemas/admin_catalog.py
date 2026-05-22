from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AdminCatalogHealthResponse(BaseModel):
    status: str
    module: str
    surface: str


class AdminUnit(BaseModel):
    id: int
    unit_code: str
    name: str
    unit_type: str
    symbol: str | None
    precision: int
    is_base_unit: bool
    base_unit_code: str | None
    conversion_factor: Decimal | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminUnitsResponse(BaseModel):
    count: int = Field(..., ge=0)
    units: list[AdminUnit]


class AdminPriceList(BaseModel):
    id: int
    price_list_code: str
    name: str
    currency: str
    region_code: str
    channel: str
    customer_segment: str
    priority: int
    is_default: bool
    is_active: bool
    effective_from: datetime | None
    effective_to: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminPriceListsResponse(BaseModel):
    count: int = Field(..., ge=0)
    price_lists: list[AdminPriceList]


class AdminProduct(BaseModel):
    id: int
    product_code: str
    name: str
    subtitle: str | None
    description: str
    category_id: int
    category_code: str
    category_name: str
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminProductsResponse(BaseModel):
    count: int = Field(..., ge=0)
    products: list[AdminProduct]


class AdminSku(BaseModel):
    id: int
    product_id: int
    product_code: str
    sku_code: str
    name: str
    legacy_price_cents: int
    legacy_currency: str
    storefront_price_cents: int | None
    storefront_currency: str | None
    stock_status: str
    image_url: str | None
    sales_unit_id: int
    sales_unit_code: str
    sales_unit_name: str
    package_quantity: Decimal
    package_unit_text: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class AdminSkusResponse(BaseModel):
    count: int = Field(..., ge=0)
    skus: list[AdminSku]


class AdminSkuPrice(BaseModel):
    id: int
    price_list_id: int
    price_list_code: str
    price_list_name: str
    channel: str
    customer_segment: str
    sku_id: int
    sku_code: str
    product_id: int
    product_code: str
    price_cents: int
    compare_at_price_cents: int | None
    currency: str
    effective_from: datetime | None
    effective_to: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminSkuPricesResponse(BaseModel):
    count: int = Field(..., ge=0)
    sku_prices: list[AdminSkuPrice]
