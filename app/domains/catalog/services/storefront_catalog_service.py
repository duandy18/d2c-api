"""Storefront catalog service backed by terminal Offer snapshots."""

from sqlalchemy.orm import Session

from app.domains.catalog.contracts.storefront_catalog_contract import (
    CatalogCategoriesResponse,
    CatalogCategory,
    CatalogProduct,
    CatalogProductsResponse,
)
from app.domains.catalog.repos.storefront_catalog_repo import (
    PublishedCatalogRow,
    get_active_catalog_row_by_offer_code,
    list_active_catalog_rows,
    list_active_categories,
)
from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPrice,
)


def _category_name(group: PublishedGroup | None) -> str:
    if group is None:
        return "全部商品"
    return group.group_name or group.group_code


def _description(offer: PublishedOffer) -> str:
    return offer.description or offer.subtitle or offer.title


def _build_tags(
    offer: PublishedOffer,
    group: PublishedGroup | None,
) -> list[str]:
    tags: list[str] = []

    category = _category_name(group)
    if category:
        tags.append(category)

    if offer.offer_type:
        tags.append(offer.offer_type)

    return tags


def _build_product_schema(
    offer: PublishedOffer,
    price: PublishedOfferPrice,
    group: PublishedGroup | None,
) -> CatalogProduct:
    return CatalogProduct(
        product_id=offer.offer_code,
        sku=offer.offer_code,
        name=offer.title,
        category=_category_name(group),
        description=_description(offer),
        price_cents=price.price_cents,
        currency=price.currency,
        tags=_build_tags(offer, group),
        status="active",
        stock_status="in_stock",
        image_url=offer.image_url,
    )


def list_catalog_categories(session: Session) -> CatalogCategoriesResponse:
    categories = [
        CatalogCategory(
            code=group_code,
            name=group_name,
            sort_order=sort_order,
        )
        for group_code, group_name, sort_order in list_active_categories(session)
    ]
    return CatalogCategoriesResponse(count=len(categories), categories=categories)


def list_catalog_products(session: Session) -> CatalogProductsResponse:
    seen_offer_codes: set[str] = set()
    products: list[CatalogProduct] = []

    for offer, price, group in list_active_catalog_rows(session):
        if offer.offer_code in seen_offer_codes:
            continue

        seen_offer_codes.add(offer.offer_code)
        products.append(_build_product_schema(offer, price, group))

    return CatalogProductsResponse(count=len(products), products=products)


def get_catalog_product(session: Session, product_id: str) -> CatalogProduct | None:
    row: PublishedCatalogRow | None = get_active_catalog_row_by_offer_code(session, product_id)

    if row is None:
        return None

    offer, price, group = row
    return _build_product_schema(offer, price, group)
