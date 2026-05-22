from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.catalog import Product, ProductCategory, ProductSku


def _base_catalog_query() -> Select[tuple[Product, ProductCategory, ProductSku]]:
    return (
        select(Product, ProductCategory, ProductSku)
        .join(ProductCategory, Product.category_id == ProductCategory.id)
        .join(ProductSku, ProductSku.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .where(Product.status == "active")
        .where(ProductCategory.is_active.is_(True))
        .where(ProductSku.is_active.is_(True))
        .order_by(ProductCategory.sort_order, Product.id, ProductSku.sort_order)
    )


def list_active_categories(session: Session) -> list[ProductCategory]:
    statement = (
        select(ProductCategory)
        .where(ProductCategory.is_active.is_(True))
        .order_by(ProductCategory.sort_order, ProductCategory.id)
    )
    return list(session.scalars(statement).all())


def list_active_catalog_rows(session: Session) -> list[tuple[Product, ProductCategory, ProductSku]]:
    return list(session.execute(_base_catalog_query()).all())


def get_active_catalog_row_by_product_code(
    session: Session,
    product_code: str,
) -> tuple[Product, ProductCategory, ProductSku] | None:
    statement = _base_catalog_query().where(Product.product_code == product_code)
    return session.execute(statement).first()
