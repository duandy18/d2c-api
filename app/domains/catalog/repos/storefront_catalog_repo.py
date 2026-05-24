"""Storefront catalog repositories.

The public storefront catalog is backed by the published runtime model.
Legacy owner-like catalog tables are not part of the storefront read path anymore.
"""

from __future__ import annotations

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedPrice,
    PublishedProduct,
    PublishedSku,
)

PublishedCatalogRow = tuple[PublishedProduct, PublishedSku, PublishedPrice]
PublishedCategoryRow = tuple[str, str, int]


def _latest_catalog_publish_version(session: Session) -> str | None:
    statement = (
        select(PublishedProduct.publish_version)
        .where(PublishedProduct.display_status == "visible")
        .where(PublishedProduct.sell_status == "sellable")
        .order_by(PublishedProduct.published_at.desc(), PublishedProduct.id.desc())
        .limit(1)
    )
    return session.scalar(statement)


def _published_product_filters() -> tuple[object, ...]:
    return (
        PublishedProduct.display_status == "visible",
        PublishedProduct.sell_status == "sellable",
        or_(PublishedProduct.visible_from.is_(None), PublishedProduct.visible_from <= func.now()),
        or_(PublishedProduct.visible_until.is_(None), PublishedProduct.visible_until > func.now()),
    )


def _published_price_filters() -> tuple[object, ...]:
    return (
        PublishedPrice.channel == "storefront",
        PublishedPrice.is_active.is_(True),
        or_(PublishedPrice.effective_from.is_(None), PublishedPrice.effective_from <= func.now()),
        or_(PublishedPrice.effective_until.is_(None), PublishedPrice.effective_until > func.now()),
    )


def _base_catalog_query(
    publish_version: str,
) -> Select[tuple[PublishedProduct, PublishedSku, PublishedPrice]]:
    return (
        select(PublishedProduct, PublishedSku, PublishedPrice)
        .join(
            PublishedSku,
            and_(
                PublishedSku.publish_version == PublishedProduct.publish_version,
                PublishedSku.product_code == PublishedProduct.product_code,
            ),
        )
        .join(
            PublishedPrice,
            and_(
                PublishedPrice.publish_version == PublishedSku.publish_version,
                PublishedPrice.sku_code == PublishedSku.sku_code,
            ),
        )
        .where(PublishedProduct.publish_version == publish_version)
        .where(PublishedSku.publish_version == publish_version)
        .where(PublishedPrice.publish_version == publish_version)
        .where(*_published_product_filters())
        .where(PublishedSku.is_sellable.is_(True))
        .where(*_published_price_filters())
        .order_by(
            PublishedProduct.sort_order,
            PublishedProduct.id,
            PublishedSku.sort_order,
            PublishedSku.id,
            PublishedPrice.priority,
            PublishedPrice.id,
        )
    )


def list_active_categories(session: Session) -> list[PublishedCategoryRow]:
    publish_version = _latest_catalog_publish_version(session)

    if publish_version is None:
        return []

    statement = (
        select(
            PublishedProduct.category_code,
            PublishedProduct.category_name,
            func.min(PublishedProduct.sort_order).label("sort_order"),
        )
        .where(PublishedProduct.publish_version == publish_version)
        .where(*_published_product_filters())
        .where(PublishedProduct.category_code.is_not(None))
        .where(PublishedProduct.category_name.is_not(None))
        .group_by(PublishedProduct.category_code, PublishedProduct.category_name)
        .order_by(func.min(PublishedProduct.sort_order), PublishedProduct.category_name)
    )

    rows = session.execute(statement).all()
    return [
        (
            str(category_code),
            str(category_name),
            int(sort_order or 0),
        )
        for category_code, category_name, sort_order in rows
    ]


def list_active_catalog_rows(session: Session) -> list[PublishedCatalogRow]:
    publish_version = _latest_catalog_publish_version(session)

    if publish_version is None:
        return []

    rows = session.execute(_base_catalog_query(publish_version)).all()
    return [(product, sku, price) for product, sku, price in rows]


def get_active_catalog_row_by_product_code(
    session: Session,
    product_code: str,
) -> PublishedCatalogRow | None:
    publish_version = _latest_catalog_publish_version(session)

    if publish_version is None:
        return None

    statement = _base_catalog_query(publish_version).where(
        PublishedProduct.product_code == product_code
    )
    row = session.execute(statement).first()

    if row is None:
        return None

    product, sku, price = row
    return product, sku, price
