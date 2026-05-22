"""Storefront catalog service."""

from sqlalchemy.orm import Session

from app.domains.catalog.contracts.storefront_catalog_contract import (
    CatalogCategoriesResponse,
    CatalogCategory,
    CatalogProduct,
    CatalogProductsResponse,
)
from app.domains.catalog.models.catalog import Product, ProductCategory, ProductSku, SkuPrice
from app.domains.catalog.repos.storefront_catalog_repo import (
    get_active_catalog_row_by_product_code,
    list_active_catalog_rows,
    list_active_categories,
)


def _build_product_schema(
    product: Product,
    category: ProductCategory,
    sku: ProductSku,
    sku_price: SkuPrice,
) -> CatalogProduct:
    return CatalogProduct(
        product_id=product.product_code,
        sku=sku.sku_code,
        name=product.name,
        category=category.name,
        description=product.description,
        price_cents=sku_price.price_cents,
        currency=sku_price.currency,
        tags=[category.name],
        status="active",
        stock_status=sku.stock_status,  # type: ignore[arg-type]
        image_url=sku.image_url,
    )


def list_catalog_categories(session: Session) -> CatalogCategoriesResponse:
    categories = [
        CatalogCategory(
            code=category.code,
            name=category.name,
            sort_order=category.sort_order,
        )
        for category in list_active_categories(session)
    ]
    return CatalogCategoriesResponse(count=len(categories), categories=categories)


def list_catalog_products(session: Session) -> CatalogProductsResponse:
    products = [
        _build_product_schema(product, category, sku, sku_price)
        for product, category, sku, sku_price in list_active_catalog_rows(session)
    ]
    return CatalogProductsResponse(count=len(products), products=products)


def get_catalog_product(session: Session, product_id: str) -> CatalogProduct | None:
    row = get_active_catalog_row_by_product_code(session, product_id)

    if row is None:
        return None

    product, category, sku, sku_price = row
    return _build_product_schema(product, category, sku, sku_price)
