"""Cart domain repositories."""

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.orm import Session

from app.domains.cart.models.cart import Cart, CartLine
from app.domains.catalog.models.catalog import PriceList, Product, ProductSku, SkuPrice


def get_active_cart(
    session: Session,
    anonymous_id: str,
    session_code: str,
) -> Cart | None:
    statement = (
        select(Cart)
        .where(Cart.status == "active")
        .where(Cart.anonymous_id == anonymous_id)
        .where(Cart.session_code == session_code)
        .order_by(Cart.id.desc())
    )
    return session.scalar(statement)


def create_cart(session: Session, cart: Cart) -> Cart:
    session.add(cart)
    session.flush()
    return cart


def _cart_lines_query(cart_id: int) -> Select[tuple[CartLine, Product, ProductSku]]:
    return (
        select(CartLine, Product, ProductSku)
        .join(Product, Product.id == CartLine.product_id)
        .join(ProductSku, ProductSku.id == CartLine.sku_id)
        .where(CartLine.cart_id == cart_id)
        .order_by(CartLine.id)
    )


def list_cart_line_rows(
    session: Session,
    cart_id: int,
) -> list[tuple[CartLine, Product, ProductSku]]:
    return list(session.execute(_cart_lines_query(cart_id)).all())


def get_product_sku_for_cart(
    session: Session,
    product_code: str,
    sku_code: str,
) -> tuple[Product, ProductSku, SkuPrice] | None:
    statement = (
        select(Product, ProductSku, SkuPrice)
        .join(ProductSku, ProductSku.product_id == Product.id)
        .join(SkuPrice, SkuPrice.sku_id == ProductSku.id)
        .join(PriceList, PriceList.id == SkuPrice.price_list_id)
        .where(Product.product_code == product_code)
        .where(ProductSku.sku_code == sku_code)
        .where(Product.is_active.is_(True))
        .where(Product.status == "active")
        .where(ProductSku.is_active.is_(True))
        .where(PriceList.price_list_code == "default_usd_storefront")
        .where(PriceList.channel == "storefront")
        .where(PriceList.customer_segment == "default")
        .where(PriceList.is_active.is_(True))
        .where(SkuPrice.is_active.is_(True))
        .where(or_(SkuPrice.effective_from.is_(None), SkuPrice.effective_from <= func.now()))
        .where(or_(SkuPrice.effective_to.is_(None), SkuPrice.effective_to > func.now()))
    )
    return session.execute(statement).first()


def get_cart_line_by_sku(
    session: Session,
    cart_id: int,
    sku_id: int,
) -> CartLine | None:
    statement = select(CartLine).where(CartLine.cart_id == cart_id).where(CartLine.sku_id == sku_id)
    return session.scalar(statement)


def create_cart_line(session: Session, cart_line: CartLine) -> CartLine:
    session.add(cart_line)
    session.flush()
    return cart_line


def delete_cart_line(session: Session, cart_line: CartLine) -> None:
    session.delete(cart_line)
    session.flush()


def clear_cart_lines(session: Session, cart_id: int) -> None:
    session.execute(delete(CartLine).where(CartLine.cart_id == cart_id))
    session.flush()
