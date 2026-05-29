"""Storefront order service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.cart.models.cart import Cart
from app.domains.customers.models.customer import Customer
from app.domains.customers.repos.customer_repo import get_active_customer_by_session_token_hash
from app.domains.orders.contracts.storefront_order_contract import (
    OrderCheckoutRequest,
    OrderLineResponse,
    OrderListResponse,
    OrderResponse,
    OrderSummaryResponse,
    PaymentResponse,
)
from app.domains.orders.models.order import D2COrder, D2COrderLine, D2CPayment
from app.domains.orders.repos.order_repo import (
    create_order,
    create_order_line,
    create_payment,
    get_cart_by_code,
    get_latest_payment_by_order_id,
    get_order_by_no_for_customer,
    list_cart_lines_for_checkout,
    list_order_lines,
    list_orders_by_customer,
)
from app.domains.promotions.models.promotion import CustomerCoupon
from app.domains.promotions.repos.checkout_promotion_repo import (
    count_coupon_used,
    count_customer_coupon_used,
    create_customer_coupon_usage,
    get_active_public_coupon_promotion_by_code,
    get_best_active_all_store_percentage_promotion,
)
from app.domains.published.models.published import PublishedCoupon, PublishedPromotionRule
from app.security.passwords import hash_session_token


class OrderAuthError(Exception):
    pass


class CheckoutCartNotFoundError(Exception):
    pass


class CheckoutCartAlreadyConvertedError(Exception):
    pass


class CheckoutCartEmptyError(Exception):
    pass


class CheckoutCouponNotAvailableError(Exception):
    pass


class CheckoutCouponUsageLimitExceededError(Exception):
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


def _new_customer_coupon_code() -> str:
    date_part = datetime.now(UTC).strftime("%Y%m%d")
    return f"CCPN-{date_part}-{uuid4().hex[:12].upper()}"


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
    rows: list[object],
) -> None:
    cart.line_count = len(rows)
    cart.item_count = sum(cart_line.quantity for cart_line in rows)
    cart.subtotal_cents = sum(cart_line.line_subtotal_cents for cart_line in rows)


def _normalize_coupon_code(coupon_code: str | None) -> str | None:
    if coupon_code is None:
        return None

    normalized = coupon_code.strip()
    return normalized or None


def _ensure_coupon_usage_allowed(
    session: Session,
    *,
    coupon: PublishedCoupon,
    customer_id: int,
) -> None:
    if (
        coupon.total_limit is not None
        and count_coupon_used(session, coupon.coupon_code) >= coupon.total_limit
    ):
        raise CheckoutCouponUsageLimitExceededError("checkout_coupon_usage_limit_exceeded")

    if (
        coupon.per_customer_limit is not None
        and count_customer_coupon_used(
            session,
            coupon_code=coupon.coupon_code,
            customer_id=customer_id,
        )
        >= coupon.per_customer_limit
    ):
        raise CheckoutCouponUsageLimitExceededError("checkout_coupon_usage_limit_exceeded")


def _calculate_percentage_discount_cents(
    subtotal_cents: int,
    promotion: PublishedPromotionRule | None,
) -> int:
    if promotion is None:
        return 0

    discount_cents = subtotal_cents * promotion.discount_value // 100

    if promotion.max_discount_cents is not None:
        discount_cents = min(discount_cents, promotion.max_discount_cents)

    return min(discount_cents, subtotal_cents)


def _build_line_response(line: D2COrderLine) -> OrderLineResponse:
    return OrderLineResponse(
        offer_code=line.offer_code,
        offer_title=line.offer_title,
        offer_type=line.offer_type,
        group_code=line.group_code,
        group_name=line.group_name,
        price_code=line.price_code,
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
        discount_cents=order.discount_cents,
        payable_cents=order.payable_cents,
        promotion_code=order.promotion_code,
        coupon_code=order.coupon_code,
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



def _build_order_summary_response(
    session: Session,
    order: D2COrder,
) -> OrderSummaryResponse:
    payment = get_latest_payment_by_order_id(session, order.id)

    return OrderSummaryResponse(
        order_no=order.order_no,
        status=order.status,
        payment_status=payment.status if payment is not None else None,
        currency=order.currency,
        item_count=order.item_count,
        subtotal_cents=order.subtotal_cents,
        discount_cents=order.discount_cents,
        payable_cents=order.payable_cents,
        paid_at=order.paid_at,
        created_at=order.created_at,
    )


def list_customer_orders(
    session: Session,
    access_token: str,
) -> OrderListResponse:
    customer = authenticate_customer(session, access_token)
    orders = list_orders_by_customer(session, customer.id)

    summaries = [_build_order_summary_response(session, order) for order in orders]

    return OrderListResponse(orders=summaries, count=len(summaries))


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

    rows = list_cart_lines_for_checkout(session, cart.id)
    _sync_cart_summary(cart, rows)

    if cart.line_count <= 0 or cart.item_count <= 0:
        raise CheckoutCartEmptyError("checkout_cart_empty")

    now = datetime.now(UTC)
    coupon: PublishedCoupon | None = None
    promotion: PublishedPromotionRule | None = None
    coupon_code = _normalize_coupon_code(payload.coupon_code)

    if coupon_code is not None:
        coupon_row = get_active_public_coupon_promotion_by_code(
            session,
            coupon_code=coupon_code,
            currency=cart.currency,
            subtotal_cents=cart.subtotal_cents,
            now=now,
        )
        if coupon_row is None:
            raise CheckoutCouponNotAvailableError("checkout_coupon_not_available")
        coupon, promotion = coupon_row
        _ensure_coupon_usage_allowed(
            session,
            coupon=coupon,
            customer_id=customer.id,
        )
    else:
        promotion = get_best_active_all_store_percentage_promotion(
            session,
            currency=cart.currency,
            subtotal_cents=cart.subtotal_cents,
            now=now,
        )

    discount_cents = _calculate_percentage_discount_cents(
        cart.subtotal_cents,
        promotion,
    )
    payable_cents = cart.subtotal_cents - discount_cents

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
            discount_cents=discount_cents,
            payable_cents=payable_cents,
            promotion_code=promotion.promotion_code if promotion is not None else None,
            promotion_name=promotion.promotion_name if promotion is not None else None,
            promotion_type=promotion.promotion_type if promotion is not None else None,
            promotion_discount_type=promotion.discount_type if promotion is not None else None,
            promotion_discount_value=promotion.discount_value if promotion is not None else None,
            promotion_publish_version=(
                promotion.publish_version if promotion is not None else None
            ),
            coupon_code=coupon.coupon_code if coupon is not None else None,
            coupon_name=coupon.coupon_name if coupon is not None else None,
            coupon_type=coupon.coupon_type if coupon is not None else None,
            coupon_publish_version=coupon.publish_version if coupon is not None else None,
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

    if coupon is not None and promotion is not None:
        create_customer_coupon_usage(
            session,
            CustomerCoupon(
                customer_coupon_code=_new_customer_coupon_code(),
                publish_version=coupon.publish_version,
                coupon_code=coupon.coupon_code,
                coupon_name=coupon.coupon_name,
                coupon_type=coupon.coupon_type,
                promotion_code=promotion.promotion_code,
                promotion_name=promotion.promotion_name,
                promotion_type=promotion.promotion_type,
                promotion_discount_type=promotion.discount_type,
                promotion_discount_value=promotion.discount_value,
                customer_id=customer.id,
                status="used",
                claimed_at=now,
                used_at=now,
                order_id=order.id,
                order_no=order.order_no,
            ),
        )

    for cart_line in rows:
        create_order_line(
            session,
            D2COrderLine(
                order_id=order.id,
                product_id=None,
                sku_id=None,
                publish_version=cart_line.publish_version,
                offer_code=cart_line.offer_code,
                offer_title=cart_line.offer_title,
                offer_type=cart_line.offer_type,
                offer_subtitle=cart_line.offer_subtitle,
                offer_image_url=cart_line.offer_image_url,
                group_code=cart_line.group_code,
                group_name=cart_line.group_name,
                price_code=cart_line.price_code,
                source_offer_id=cart_line.source_offer_id,
                source_position_id=cart_line.source_position_id,
                product_code=cart_line.product_code,
                sku_code=cart_line.sku_code,
                product_name=cart_line.product_name,
                sku_name=cart_line.sku_name,
                pms_item_id=cart_line.pms_item_id,
                pms_sku=cart_line.pms_sku,
                category_code=cart_line.category_code,
                category_name=cart_line.category_name,
                brand_code=cart_line.brand_code,
                brand_name=cart_line.brand_name,
                sales_unit_code=cart_line.sales_unit_code,
                sales_unit_name=cart_line.sales_unit_name,
                barcode=cart_line.barcode,
                spec_text=cart_line.spec_text,
                price_list_code=cart_line.price_list_code,
                compare_at_price_cents=cart_line.compare_at_price_cents,
                source_product_id=cart_line.source_product_id,
                source_sku_id=cart_line.source_sku_id,
                source_price_id=cart_line.source_price_id,
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
            amount_cents=order.payable_cents,
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
