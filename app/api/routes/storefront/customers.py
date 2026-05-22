"""Storefront customer routes; HTTP paths remain /customers/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.customers.contracts.storefront_customer_contract import (
    CustomerAuthResponse,
    CustomerLoginRequest,
    CustomerRegisterRequest,
)
from app.domains.customers.services.storefront_customer_service import (
    CustomerAuthError,
    CustomerConflictError,
    login_customer,
    register_customer,
)

router = APIRouter(prefix="/customers", tags=["customers"])
SessionDep = Annotated[Session, Depends(get_session)]


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
