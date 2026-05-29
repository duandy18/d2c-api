"""Storefront customer routes; HTTP paths remain /customers/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.customers.contracts.storefront_customer_contract import (
    CustomerAuthResponse,
    CustomerLoginRequest,
    CustomerLogoutResponse,
    CustomerProfile,
    CustomerRegisterRequest,
)
from app.domains.customers.services.storefront_customer_service import (
    CustomerAuthError,
    CustomerConflictError,
    get_current_customer,
    login_customer,
    logout_customer,
    register_customer,
)

router = APIRouter(prefix="/customers", tags=["customers"])
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


@router.get("/health")
def customers_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "customers",
        "auth_mode": "password",
    }


@router.post(
    "/register",
    response_model=CustomerAuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def customers_register(
    payload: CustomerRegisterRequest,
    session: SessionDep,
) -> CustomerAuthResponse:
    try:
        return register_customer(session, payload)
    except CustomerConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/login", response_model=CustomerAuthResponse)
def customers_login(
    payload: CustomerLoginRequest,
    session: SessionDep,
) -> CustomerAuthResponse:
    try:
        return login_customer(session, payload)
    except CustomerAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.get("/me", response_model=CustomerProfile)
def customers_me(
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CustomerProfile:
    access_token = _extract_access_token(authorization)

    try:
        return get_current_customer(session, access_token)
    except CustomerAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


@router.post("/logout", response_model=CustomerLogoutResponse)
def customers_logout(
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CustomerLogoutResponse:
    access_token = _extract_access_token(authorization)

    try:
        return logout_customer(session, access_token)
    except CustomerAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
