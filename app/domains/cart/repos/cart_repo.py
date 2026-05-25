"""Cart domain repositories."""

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.domains.cart.models.cart import Cart, CartLine
from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferComponent,
    PublishedOfferPosition,
    PublishedOfferPrice,
)

PublishedCartItem = tuple[
    PublishedOffer,
    PublishedOfferPrice,
    PublishedOfferComponent | None,
    PublishedGroup | None,
    PublishedOfferPosition | None,
]


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


def _published_offer_filters() -> tuple[object, ...]:
    return (
        PublishedOffer.display_status == "visible",
        PublishedOffer.sell_status == "sellable",
    )


def _published_price_filters() -> tuple[object, ...]:
    return (
        PublishedOfferPrice.channel == "storefront",
        PublishedOfferPrice.is_active.is_(True),
        or_(
            PublishedOfferPrice.effective_from.is_(None),
            PublishedOfferPrice.effective_from <= func.now(),
        ),
        or_(
            PublishedOfferPrice.effective_until.is_(None),
            PublishedOfferPrice.effective_until > func.now(),
        ),
    )


def _published_position_filters() -> tuple[object, ...]:
    return (
        PublishedOfferPosition.is_active.is_(True),
        or_(
            PublishedOfferPosition.visible_from.is_(None),
            PublishedOfferPosition.visible_from <= func.now(),
        ),
        or_(
            PublishedOfferPosition.visible_until.is_(None),
            PublishedOfferPosition.visible_until > func.now(),
        ),
    )


def _published_cart_item_query(
    offer_code: str,
) -> Select[
    tuple[
        PublishedOffer,
        PublishedOfferPrice,
        PublishedOfferComponent | None,
        PublishedGroup | None,
        PublishedOfferPosition | None,
    ]
]:
    return (
        select(
            PublishedOffer,
            PublishedOfferPrice,
            PublishedOfferComponent,
            PublishedGroup,
            PublishedOfferPosition,
        )
        .join(
            PublishedOfferPrice,
            and_(
                PublishedOfferPrice.publish_version == PublishedOffer.publish_version,
                PublishedOfferPrice.offer_code == PublishedOffer.offer_code,
            ),
        )
        .outerjoin(
            PublishedOfferComponent,
            and_(
                PublishedOfferComponent.publish_version == PublishedOffer.publish_version,
                PublishedOfferComponent.offer_code == PublishedOffer.offer_code,
                PublishedOfferComponent.component_no == 1,
            ),
        )
        .outerjoin(
            PublishedOfferPosition,
            and_(
                PublishedOfferPosition.publish_version == PublishedOffer.publish_version,
                PublishedOfferPosition.offer_code == PublishedOffer.offer_code,
            ),
        )
        .outerjoin(
            PublishedGroup,
            and_(
                PublishedGroup.publish_version == PublishedOfferPosition.publish_version,
                PublishedGroup.group_code == PublishedOfferPosition.group_code,
            ),
        )
        .where(PublishedOffer.offer_code == offer_code)
        .where(*_published_offer_filters())
        .where(*_published_price_filters())
        .where(or_(PublishedOfferPosition.id.is_(None), *_published_position_filters()))
        .order_by(
            PublishedOffer.published_at.desc(),
            PublishedOffer.id.desc(),
            PublishedGroup.sort_order.nullslast(),
            PublishedOfferPosition.sort_order.nullslast(),
            PublishedOfferPrice.priority,
            PublishedOfferPrice.id,
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
    offer_code: str,
) -> PublishedCartItem | None:
    return session.execute(_published_cart_item_query(offer_code)).first()


def get_cart_line_by_published_offer(
    session: Session,
    cart_id: int,
    publish_version: str,
    offer_code: str,
) -> CartLine | None:
    statement = (
        select(CartLine)
        .where(CartLine.cart_id == cart_id)
        .where(CartLine.publish_version == publish_version)
        .where(CartLine.offer_code == offer_code)
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
