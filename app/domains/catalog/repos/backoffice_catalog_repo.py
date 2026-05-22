"""Backoffice catalog repositories."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.catalog.models.catalog import (
    PriceList,
    Product,
    ProductCategory,
    ProductSku,
    SkuPrice,
    Unit,
)


def list_units(session: Session) -> list[Unit]:
    statement = select(Unit).order_by(Unit.sort_order, Unit.id)
    return list(session.scalars(statement).all())


def list_price_lists(session: Session) -> list[PriceList]:
    statement = select(PriceList).order_by(
        PriceList.is_default.desc(),
        PriceList.priority,
        PriceList.id,
    )
    return list(session.scalars(statement).all())


def list_product_rows(
    session: Session,
) -> list[tuple[Product, ProductCategory]]:
    statement = (
        select(Product, ProductCategory)
        .join(ProductCategory, Product.category_id == ProductCategory.id)
        .order_by(ProductCategory.sort_order, Product.id)
    )
    return list(session.execute(statement).all())


def list_sku_rows(
    session: Session,
) -> list[tuple[ProductSku, Product, Unit, SkuPrice | None]]:
    statement = (
        select(ProductSku, Product, Unit, SkuPrice)
        .join(Product, Product.id == ProductSku.product_id)
        .join(Unit, Unit.id == ProductSku.sales_unit_id)
        .outerjoin(SkuPrice, SkuPrice.sku_id == ProductSku.id)
        .outerjoin(PriceList, PriceList.id == SkuPrice.price_list_id)
        .where((PriceList.price_list_code == "default_usd_storefront") | (PriceList.id.is_(None)))
        .order_by(Product.id, ProductSku.sort_order, ProductSku.id)
    )
    return list(session.execute(statement).all())


def list_sku_price_rows(
    session: Session,
) -> list[tuple[SkuPrice, PriceList, ProductSku, Product]]:
    statement = (
        select(SkuPrice, PriceList, ProductSku, Product)
        .join(PriceList, PriceList.id == SkuPrice.price_list_id)
        .join(ProductSku, ProductSku.id == SkuPrice.sku_id)
        .join(Product, Product.id == ProductSku.product_id)
        .order_by(
            PriceList.is_default.desc(),
            PriceList.priority,
            PriceList.id,
            Product.id,
            ProductSku.sort_order,
            ProductSku.id,
        )
    )
    return list(session.execute(statement).all())
