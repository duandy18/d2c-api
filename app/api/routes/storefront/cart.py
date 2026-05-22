"""Storefront cart routes; HTTP paths remain /cart/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.cart.contracts.storefront_cart_contract import (
    CartIdentityRequest,
    CartItemUpsertRequest,
    CartResponse,
)
from app.domains.cart.services.storefront_cart_service import (
    CartProductNotFoundError,
    clear_cart,
    get_cart,
    upsert_cart_item,
)

router = APIRouter(prefix="/cart", tags=["cart"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/health")
def cart_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "cart",
        "storage": "d2c_carts",
    }


@router.get("", response_model=CartResponse)
def cart_detail(
    anonymous_id: Annotated[str, Query(min_length=8, max_length=96)],
    session_code: Annotated[str, Query(min_length=8, max_length=96)],
    session: SessionDep,
) -> CartResponse:
    return get_cart(
        session,
        CartIdentityRequest(
            anonymous_id=anonymous_id,
            session_code=session_code,
        ),
    )


@router.post("/items", response_model=CartResponse)
def cart_items_upsert(
    payload: CartItemUpsertRequest,
    session: SessionDep,
) -> CartResponse:
    try:
        return upsert_cart_item(session, payload)
    except CartProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/clear", response_model=CartResponse)
def cart_clear(
    payload: CartIdentityRequest,
    session: SessionDep,
) -> CartResponse:
    return clear_cart(session, payload)
