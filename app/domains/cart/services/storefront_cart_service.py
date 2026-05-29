"""Storefront cart service backed by terminal Offer snapshots."""

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
    get_cart_line_by_published_offer,
    get_published_item_for_cart,
    list_cart_lines,
)
from app.domains.site_config.repos.storefront_site_config_repo import get_offer_display_metric


class CartOfferNotFoundError(Exception):
    pass


class CartOfferDisplayStockUnavailableError(Exception):
    pass


class CartOfferQuantityExceedsDisplayStockError(Exception):
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
        offer_code=cart_line.offer_code or cart_line.product_code,
        name=cart_line.offer_title or cart_line.product_name,
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
    offer, _price, component, _group, _position = published_item
    product_name = offer.title
    sku_name = component.sku_code if component is not None else offer.title
    return product_name, sku_name


def _legacy_sku_code(published_item: PublishedCartItem) -> str:
    offer, _price, component, _group, _position = published_item
    return component.sku_code if component is not None else offer.offer_code


def _ensure_display_stock_quantity_allowed(
    session: Session,
    *,
    offer_code: str,
    quantity: int,
) -> None:
    if quantity <= 0:
        return

    metric = get_offer_display_metric(session, offer_code)

    if metric is None or not metric.is_active:
        raise CartOfferDisplayStockUnavailableError("cart_offer_display_stock_unavailable")

    if metric.display_stock_quantity <= 0:
        raise CartOfferDisplayStockUnavailableError("cart_offer_display_stock_unavailable")

    if quantity > metric.display_stock_quantity:
        raise CartOfferQuantityExceedsDisplayStockError(
            "cart_offer_quantity_exceeds_display_stock"
        )


def _apply_published_snapshot(
    cart_line: CartLine,
    published_item: PublishedCartItem,
) -> None:
    offer, price, component, group, position = published_item
    product_name, sku_name = _line_names(published_item)

    cart_line.product_id = None
    cart_line.sku_id = None
    cart_line.publish_version = offer.publish_version

    cart_line.offer_code = offer.offer_code
    cart_line.offer_title = offer.title
    cart_line.offer_type = offer.offer_type
    cart_line.offer_subtitle = offer.subtitle
    cart_line.offer_image_url = offer.image_url
    cart_line.group_code = group.group_code if group is not None else None
    cart_line.group_name = group.group_name if group is not None else None
    cart_line.price_code = price.price_code
    cart_line.source_offer_id = offer.source_offer_id
    cart_line.source_position_id = position.source_position_id if position is not None else None

    # Transitional internal snapshot fields used by checkout/order until the next cut.
    cart_line.product_code = offer.offer_code
    cart_line.sku_code = _legacy_sku_code(published_item)
    cart_line.product_name = product_name
    cart_line.sku_name = sku_name

    cart_line.pms_item_id = component.pms_item_id if component is not None else None
    cart_line.pms_sku = component.pms_sku if component is not None else None
    cart_line.category_code = group.group_code if group is not None else None
    cart_line.category_name = group.group_name if group is not None else None
    cart_line.brand_code = None
    cart_line.brand_name = None
    cart_line.sales_unit_code = component.uom_code if component is not None else None
    cart_line.sales_unit_name = component.uom_name if component is not None else None
    cart_line.barcode = component.barcode if component is not None else None
    cart_line.spec_text = None

    cart_line.price_list_code = price.price_code
    cart_line.compare_at_price_cents = price.compare_at_price_cents
    cart_line.source_product_id = offer.source_offer_id
    cart_line.source_sku_id = component.source_component_id if component is not None else None
    cart_line.source_price_id = price.source_price_id
    cart_line.unit_price_cents = price.price_cents
    cart_line.currency = price.currency


def upsert_cart_item(
    session: Session,
    payload: CartItemUpsertRequest,
) -> CartResponse:
    cart = get_or_create_cart(session, payload.anonymous_id, payload.session_code)
    published_item = get_published_item_for_cart(
        session,
        payload.offer_code,
    )

    if published_item is None:
        raise CartOfferNotFoundError("cart_offer_not_found")

    offer, price, _component, _group, _position = published_item
    _ensure_display_stock_quantity_allowed(
        session,
        offer_code=offer.offer_code,
        quantity=payload.quantity,
    )

    existing_line = get_cart_line_by_published_offer(
        session,
        cart.id,
        offer.publish_version,
        offer.offer_code,
    )

    if payload.quantity == 0:
        if existing_line is not None:
            delete_cart_line(session, existing_line)
        response = build_cart_response(session, cart)
        session.commit()
        return response

    line_subtotal_cents = price.price_cents * payload.quantity

    if existing_line is None:
        product_name, sku_name = _line_names(published_item)
        cart_line = CartLine(
            cart_id=cart.id,
            product_id=None,
            sku_id=None,
            publish_version=offer.publish_version,
            offer_code=offer.offer_code,
            offer_title=offer.title,
            product_code=offer.offer_code,
            sku_code=_legacy_sku_code(published_item),
            product_name=product_name,
            sku_name=sku_name,
            quantity=payload.quantity,
            unit_price_cents=price.price_cents,
            currency=price.currency,
            line_subtotal_cents=line_subtotal_cents,
        )
        _apply_published_snapshot(cart_line, published_item)
        create_cart_line(session, cart_line)
    else:
        _apply_published_snapshot(existing_line, published_item)
        existing_line.quantity = payload.quantity
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
