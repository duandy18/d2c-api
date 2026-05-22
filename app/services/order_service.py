from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.customer import Customer
from app.models.order import D2COrder, D2COrderLine, D2CPayment
from app.repos.customer_repo import get_active_customer_by_session_token_hash
from app.repos.order_repo import (
    create_order,
    create_order_line,
    create_payment,
    get_cart_by_code,
    get_latest_payment_by_order_id,
    get_order_by_no_for_customer,
    list_cart_line_rows_for_checkout,
    list_order_lines,
)
from app.schemas.order import (
    OrderCheckoutRequest,
    OrderLineResponse,
    OrderResponse,
    PaymentResponse,
)
from app.security.passwords import hash_session_token


class OrderAuthError(Exception):
    pass


class CheckoutCartNotFoundError(Exception):
    pass


class CheckoutCartAlreadyConvertedError(Exception):
    pass


class CheckoutCartEmptyError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


class PaymentInvalidStateError(Exception):
    pass


def _new_order_no() -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"ORD-{date_part}-{uuid4().hex[:12].upper()}"


def _new_payment_no() -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"PAY-{date_part}-{uuid4().hex[:12].upper()}"


def authenticate_customer(
    session: Session,
    access_token: str,
) -> Customer:
    customer = get_active_customer_by_session_token_hash(
        session,
        hash_session_token(access_token),
        datetime.now(UTC),
    )

    if customer is None:
        raise OrderAuthError("customer_auth_required")

    return customer


def _sync_cart_summary(
    cart: Cart,
    rows: list[tuple[object, object, object]],
) -> None:
    cart.line_count = len(rows)
    cart.item_count = sum(cart_line.quantity for cart_line, _, _ in rows)
    cart.subtotal_cents = sum(cart_line.line_subtotal_cents for cart_line, _, _ in rows)


def _build_line_response(line: D2COrderLine) -> OrderLineResponse:
    return OrderLineResponse(
        product_code=line.product_code,
        sku_code=line.sku_code,
        product_name=line.product_name,
        sku_name=line.sku_name,
        quantity=line.quantity,
        unit_price_cents=line.unit_price_cents,
        line_subtotal_cents=line.line_subtotal_cents,
    )


def _build_payment_response(payment: D2CPayment) -> PaymentResponse:
    return PaymentResponse(
        payment_no=payment.payment_no,
        provider=payment.provider,
        payment_method=payment.payment_method,
        status=payment.status,
        amount_cents=payment.amount_cents,
        currency=payment.currency,
        provider_payment_id=payment.provider_payment_id,
        provider_trade_no=payment.provider_trade_no,
        payment_reference=payment.payment_reference,
        paid_at=payment.paid_at,
        created_at=payment.created_at,
    )


def build_order_response(
    session: Session,
    order: D2COrder,
) -> OrderResponse:
    lines = list_order_lines(session, order.id)
    payment = get_latest_payment_by_order_id(session, order.id)

    return OrderResponse(
        order_no=order.order_no,
        cart_code=order.cart_code,
        status=order.status,
        currency=order.currency,
        item_count=order.item_count,
        subtotal_cents=order.subtotal_cents,
        recipient_name=order.recipient_name,
        recipient_phone=order.recipient_phone,
        shipping_country=order.shipping_country,
        shipping_province=order.shipping_province,
        shipping_city=order.shipping_city,
        shipping_district=order.shipping_district,
        shipping_address_line1=order.shipping_address_line1,
        shipping_address_line2=order.shipping_address_line2,
        shipping_postal_code=order.shipping_postal_code,
        paid_at=order.paid_at,
        created_at=order.created_at,
        lines=[_build_line_response(line) for line in lines],
        payment=_build_payment_response(payment) if payment is not None else None,
    )


def checkout_order(
    session: Session,
    access_token: str,
    payload: OrderCheckoutRequest,
) -> OrderResponse:
    customer = authenticate_customer(session, access_token)
    cart = get_cart_by_code(session, payload.cart_code)

    if cart is None:
        raise CheckoutCartNotFoundError("checkout_cart_not_found")

    if cart.status != "active":
        raise CheckoutCartAlreadyConvertedError("checkout_cart_already_converted")

    rows = list_cart_line_rows_for_checkout(session, cart.id)
    _sync_cart_summary(cart, rows)

    if cart.line_count <= 0 or cart.item_count <= 0:
        raise CheckoutCartEmptyError("checkout_cart_empty")

    cart.customer_id = customer.id

    order = create_order(
        session,
        D2COrder(
            order_no=_new_order_no(),
            customer_id=customer.id,
            cart_id=cart.id,
            cart_code=cart.cart_code,
            status="pending_payment",
            currency=cart.currency,
            item_count=cart.item_count,
            subtotal_cents=cart.subtotal_cents,
            recipient_name=payload.recipient_name,
            recipient_phone=payload.recipient_phone,
            shipping_country=payload.shipping_country,
            shipping_province=payload.shipping_province,
            shipping_city=payload.shipping_city,
            shipping_district=payload.shipping_district,
            shipping_address_line1=payload.shipping_address_line1,
            shipping_address_line2=payload.shipping_address_line2,
            shipping_postal_code=payload.shipping_postal_code,
        ),
    )

    for cart_line, product, sku in rows:
        create_order_line(
            session,
            D2COrderLine(
                order_id=order.id,
                product_id=product.id,
                sku_id=sku.id,
                product_code=product.product_code,
                sku_code=sku.sku_code,
                product_name=product.name,
                sku_name=sku.name,
                quantity=cart_line.quantity,
                unit_price_cents=cart_line.unit_price_cents,
                line_subtotal_cents=cart_line.line_subtotal_cents,
            ),
        )

    create_payment(
        session,
        D2CPayment(
            payment_no=_new_payment_no(),
            order_id=order.id,
            order_no=order.order_no,
            customer_id=customer.id,
            amount_cents=order.subtotal_cents,
            currency=order.currency,
            provider=payload.payment_provider,
            payment_method=payload.payment_method,
            status="pending",
        ),
    )

    cart.status = "converted"
    session.commit()

    return build_order_response(session, order)


def get_customer_order(
    session: Session,
    access_token: str,
    order_no: str,
) -> OrderResponse:
    customer = authenticate_customer(session, access_token)
    order = get_order_by_no_for_customer(session, order_no, customer.id)

    if order is None:
        raise OrderNotFoundError("order_not_found")

    return build_order_response(session, order)


def mark_mock_payment_succeeded(
    session: Session,
    access_token: str,
    order_no: str,
) -> OrderResponse:
    customer = authenticate_customer(session, access_token)
    order = get_order_by_no_for_customer(session, order_no, customer.id)

    if order is None:
        raise OrderNotFoundError("order_not_found")

    payment = get_latest_payment_by_order_id(session, order.id)

    if payment is None:
        raise PaymentInvalidStateError("payment_not_found")

    if order.status != "pending_payment" or payment.status != "pending":
        raise PaymentInvalidStateError("payment_invalid_state")

    if payment.provider != "mock":
        raise PaymentInvalidStateError("payment_provider_not_mock")

    paid_at = datetime.now(UTC)
    payment.status = "succeeded"
    payment.provider_payment_id = f"MOCK-{uuid4().hex[:16].upper()}"
    payment.provider_trade_no = f"MOCK-TRADE-{uuid4().hex[:16].upper()}"
    payment.payment_reference = "mock_payment_success"
    payment.paid_at = paid_at
    payment.updated_at = paid_at

    order.status = "paid"
    order.paid_at = paid_at
    order.updated_at = paid_at

    session.commit()

    return build_order_response(session, order)
