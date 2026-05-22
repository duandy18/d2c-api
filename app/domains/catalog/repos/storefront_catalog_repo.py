"""Storefront catalog repositories."""

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.domains.catalog.models.catalog import (
    PriceList,
    Product,
    ProductCategory,
    ProductSku,
    SkuPrice,
)


def _base_catalog_query() -> Select[tuple[Product, ProductCategory, ProductSku, SkuPrice]]:
    return (
        select(Product, ProductCategory, ProductSku, SkuPrice)
        .join(ProductCategory, Product.category_id == ProductCategory.id)
        .join(ProductSku, ProductSku.product_id == Product.id)
        .join(SkuPrice, SkuPrice.sku_id == ProductSku.id)
        .join(PriceList, PriceList.id == SkuPrice.price_list_id)
        .where(Product.is_active.is_(True))
        .where(Product.status == "active")
        .where(ProductCategory.is_active.is_(True))
        .where(ProductSku.is_active.is_(True))
        .where(PriceList.price_list_code == "default_usd_storefront")
        .where(PriceList.channel == "storefront")
        .where(PriceList.customer_segment == "default")
        .where(PriceList.is_active.is_(True))
        .where(SkuPrice.is_active.is_(True))
        .where(or_(SkuPrice.effective_from.is_(None), SkuPrice.effective_from <= func.now()))
        .where(or_(SkuPrice.effective_to.is_(None), SkuPrice.effective_to > func.now()))
        .order_by(ProductCategory.sort_order, Product.id, ProductSku.sort_order)
    )


def list_active_categories(session: Session) -> list[ProductCategory]:
    statement = (
        select(ProductCategory)
        .where(ProductCategory.is_active.is_(True))
        .order_by(ProductCategory.sort_order, ProductCategory.id)
    )
    return list(session.scalars(statement).all())


def list_active_catalog_rows(
    session: Session,
) -> list[tuple[Product, ProductCategory, ProductSku, SkuPrice]]:
    return list(session.execute(_base_catalog_query()).all())


def get_active_catalog_row_by_product_code(
    session: Session,
    product_code: str,
) -> tuple[Product, ProductCategory, ProductSku, SkuPrice] | None:
    statement = _base_catalog_query().where(Product.product_code == product_code)
    return session.execute(statement).first()
