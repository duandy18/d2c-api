"""Storefront order routes; HTTP paths remain /orders/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.orders.contracts.storefront_order_contract import (
    OrderCheckoutRequest,
    OrderListResponse,
    OrderResponse,
)
from app.domains.orders.services.storefront_order_service import (
    CheckoutCartAlreadyConvertedError,
    CheckoutCartEmptyError,
    CheckoutCartNotFoundError,
    CheckoutCouponNotAvailableError,
    CheckoutCouponUsageLimitExceededError,
    OrderAuthError,
    OrderNotFoundError,
    PaymentInvalidStateError,
    checkout_order,
    get_customer_order,
    list_customer_orders,
    mark_mock_payment_succeeded,
)

router = APIRouter(tags=["orders"])
SessionDep = Annotated[Session, Depends(get_session)]


def _extract_access_token(authorization: str | None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="customer_auth_required",
        )

    access_token = authorization.removeprefix("Bearer ").strip()
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="customer_auth_required",
        )
    return access_token


@router.get("/orders/health")
def orders_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "orders",
        "checkout_mode": "cart_conversion",
        "payment_mode": "mock_ready",
    }


@router.get("/orders", response_model=OrderListResponse)
def orders_list(
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> OrderListResponse:
    access_token = _extract_access_token(authorization)

    try:
        return list_customer_orders(session, access_token)
    except OrderAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post(
    "/orders/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def orders_checkout(
    payload: OrderCheckoutRequest,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> OrderResponse:
    access_token = _extract_access_token(authorization)

    try:
        return checkout_order(session, access_token, payload)
    except OrderAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except CheckoutCartNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (
        CheckoutCartAlreadyConvertedError,
        CheckoutCartEmptyError,
        CheckoutCouponNotAvailableError,
        CheckoutCouponUsageLimitExceededError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/orders/{order_no}", response_model=OrderResponse)
def orders_detail(
    order_no: str,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> OrderResponse:
    access_token = _extract_access_token(authorization)

    try:
        return get_customer_order(session, access_token, order_no)
    except OrderAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/orders/{order_no}/pay/mock", response_model=OrderResponse)
def orders_mock_pay(
    order_no: str,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> OrderResponse:
    access_token = _extract_access_token(authorization)

    try:
        return mark_mock_payment_succeeded(session, access_token, order_no)
    except OrderAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PaymentInvalidStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
