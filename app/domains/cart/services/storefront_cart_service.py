"""Storefront cart service."""

from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.cart.contracts.storefront_cart_contract import (
    CartIdentityRequest,
    CartItemUpsertRequest,
    CartLineResponse,
    CartResponse,
)
from app.domains.cart.models.cart import Cart, CartLine
from app.domains.cart.repos.cart_repo import (
    PublishedCartItem,
    clear_cart_lines,
    create_cart,
    create_cart_line,
    delete_cart_line,
    get_active_cart,
    get_cart_line_by_published_sku,
    get_published_item_for_cart,
    list_cart_lines,
)


class CartProductNotFoundError(Exception):
    pass


def _new_cart_code() -> str:
    return f"CART-{uuid4().hex[:16].upper()}"


def get_or_create_cart(
    session: Session,
    anonymous_id: str,
    session_code: str,
) -> Cart:
    cart = get_active_cart(session, anonymous_id, session_code)

    if cart is not None:
        return cart

    cart = create_cart(
        session,
        Cart(
            cart_code=_new_cart_code(),
            anonymous_id=anonymous_id,
            session_code=session_code,
            status="active",
            currency="USD",
            line_count=0,
            item_count=0,
            subtotal_cents=0,
        ),
    )
    session.commit()
    return cart


def _build_line_response(cart_line: CartLine) -> CartLineResponse:
    return CartLineResponse(
        product_id=cart_line.product_code,
        sku=cart_line.sku_code,
        name=cart_line.product_name,
        quantity=cart_line.quantity,
        unit_price_cents=cart_line.unit_price_cents,
        currency=cart_line.currency,
        line_subtotal_cents=cart_line.line_subtotal_cents,
    )


def _sync_cart_summary(
    cart: Cart,
    rows: list[CartLine],
) -> None:
    cart.line_count = len(rows)
    cart.item_count = sum(cart_line.quantity for cart_line in rows)
    cart.subtotal_cents = sum(cart_line.line_subtotal_cents for cart_line in rows)


def build_cart_response(session: Session, cart: Cart) -> CartResponse:
    rows = list_cart_lines(session, cart.id)
    _sync_cart_summary(cart, rows)
    lines = [_build_line_response(cart_line) for cart_line in rows]

    return CartResponse(
        cart_code=cart.cart_code,
        anonymous_id=cart.anonymous_id,
        session_code=cart.session_code,
        currency=cart.currency,
        line_count=cart.line_count,
        item_count=cart.item_count,
        subtotal_cents=cart.subtotal_cents,
        lines=lines,
    )


def get_cart(
    session: Session,
    payload: CartIdentityRequest,
) -> CartResponse:
    cart = get_or_create_cart(session, payload.anonymous_id, payload.session_code)
    return build_cart_response(session, cart)


def _line_names(published_item: PublishedCartItem) -> tuple[str, str]:
    product, sku, _price = published_item
    product_name = product.display_name or product.product_name
    sku_name = sku.display_sku_name or sku.sku_name
    return product_name, sku_name


def upsert_cart_item(
    session: Session,
    payload: CartItemUpsertRequest,
) -> CartResponse:
    cart = get_or_create_cart(session, payload.anonymous_id, payload.session_code)
    published_item = get_published_item_for_cart(
        session,
        payload.product_id,
        payload.sku,
    )

    if published_item is None:
        raise CartProductNotFoundError("cart_product_not_found")

    product, sku, price = published_item
    existing_line = get_cart_line_by_published_sku(
        session,
        cart.id,
        product.publish_version,
        sku.sku_code,
    )

    if payload.quantity == 0:
        if existing_line is not None:
            delete_cart_line(session, existing_line)
        response = build_cart_response(session, cart)
        session.commit()
        return response

    product_name, sku_name = _line_names(published_item)
    line_subtotal_cents = price.price_cents * payload.quantity

    if existing_line is None:
        create_cart_line(
            session,
            CartLine(
                cart_id=cart.id,
                product_id=None,
                sku_id=None,
                publish_version=product.publish_version,
                product_code=product.product_code,
                sku_code=sku.sku_code,
                product_name=product_name,
                sku_name=sku_name,
                quantity=payload.quantity,
                unit_price_cents=price.price_cents,
                currency=price.currency,
                line_subtotal_cents=line_subtotal_cents,
            ),
        )
    else:
        existing_line.product_id = None
        existing_line.sku_id = None
        existing_line.product_code = product.product_code
        existing_line.product_name = product_name
        existing_line.sku_name = sku_name
        existing_line.quantity = payload.quantity
        existing_line.unit_price_cents = price.price_cents
        existing_line.currency = price.currency
        existing_line.line_subtotal_cents = line_subtotal_cents

    response = build_cart_response(session, cart)
    session.commit()
    return response


def clear_cart(
    session: Session,
    payload: CartIdentityRequest,
) -> CartResponse:
    cart = get_or_create_cart(session, payload.anonymous_id, payload.session_code)
    clear_cart_lines(session, cart.id)
    response = build_cart_response(session, cart)
    session.commit()
    return response
