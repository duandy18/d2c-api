"""Storefront catalog service."""

from sqlalchemy.orm import Session

from app.domains.catalog.contracts.storefront_catalog_contract import (
    CatalogCategoriesResponse,
    CatalogCategory,
    CatalogProduct,
    CatalogProductsResponse,
)
from app.domains.catalog.repos.storefront_catalog_repo import (
    PublishedCatalogRow,
    get_active_catalog_row_by_product_code,
    list_active_catalog_rows,
    list_active_categories,
)
from app.domains.published.models.published import PublishedPrice, PublishedProduct, PublishedSku


def _category_name(product: PublishedProduct) -> str:
    return product.category_name or product.category_code or "未分类"


def _description(product: PublishedProduct) -> str:
    return product.description or product.product_name


def _build_tags(product: PublishedProduct) -> list[str]:
    tags: list[str] = []

    category = _category_name(product)
    if category:
        tags.append(category)

    if product.brand_name:
        tags.append(product.brand_name)

    return tags


def _build_product_schema(
    product: PublishedProduct,
    sku: PublishedSku,
    price: PublishedPrice,
) -> CatalogProduct:
    return CatalogProduct(
        product_id=product.product_code,
        sku=sku.sku_code,
        name=product.display_name,
        category=_category_name(product),
        description=_description(product),
        price_cents=price.price_cents,
        currency=price.currency,
        tags=_build_tags(product),
        status="active",
        stock_status="in_stock",
        image_url=product.image_url,
    )


def list_catalog_categories(session: Session) -> CatalogCategoriesResponse:
    categories = [
        CatalogCategory(
            code=category_code,
            name=category_name,
            sort_order=sort_order,
        )
        for category_code, category_name, sort_order in list_active_categories(session)
    ]
    return CatalogCategoriesResponse(count=len(categories), categories=categories)


def list_catalog_products(session: Session) -> CatalogProductsResponse:
    seen_product_codes: set[str] = set()
    products: list[CatalogProduct] = []

    for product, sku, price in list_active_catalog_rows(session):
        if product.product_code in seen_product_codes:
            continue

        seen_product_codes.add(product.product_code)
        products.append(_build_product_schema(product, sku, price))

    return CatalogProductsResponse(count=len(products), products=products)


def get_catalog_product(session: Session, product_id: str) -> CatalogProduct | None:
    row: PublishedCatalogRow | None = get_active_catalog_row_by_product_code(session, product_id)

    if row is None:
        return None

    product, sku, price = row
    return _build_product_schema(product, sku, price)
