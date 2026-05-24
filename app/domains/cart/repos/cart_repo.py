"""Cart domain repositories."""

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.domains.cart.models.cart import Cart, CartLine
from app.domains.published.models.published import PublishedPrice, PublishedProduct, PublishedSku

PublishedCartItem = tuple[PublishedProduct, PublishedSku, PublishedPrice]


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


def _published_cart_item_query(
    product_code: str,
    sku_code: str,
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
        .where(PublishedProduct.product_code == product_code)
        .where(PublishedSku.sku_code == sku_code)
        .where(*_published_product_filters())
        .where(PublishedSku.is_sellable.is_(True))
        .where(*_published_price_filters())
        .order_by(
            PublishedProduct.published_at.desc(),
            PublishedProduct.id.desc(),
            PublishedPrice.priority,
            PublishedPrice.id,
        )
        .limit(1)
    )


def list_cart_lines(
    session: Session,
    cart_id: int,
) -> list[CartLine]:
    statement = select(CartLine).where(CartLine.cart_id == cart_id).order_by(CartLine.id)
    return list(session.scalars(statement).all())


def get_published_item_for_cart(
    session: Session,
    product_code: str,
    sku_code: str,
) -> PublishedCartItem | None:
    return session.execute(_published_cart_item_query(product_code, sku_code)).first()


def get_cart_line_by_published_sku(
    session: Session,
    cart_id: int,
    publish_version: str,
    sku_code: str,
) -> CartLine | None:
    statement = (
        select(CartLine)
        .where(CartLine.cart_id == cart_id)
        .where(CartLine.publish_version == publish_version)
        .where(CartLine.sku_code == sku_code)
    )
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
