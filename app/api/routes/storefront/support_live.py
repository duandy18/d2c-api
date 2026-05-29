"""Storefront live support routes; HTTP paths remain /support/live/*."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.support.contracts.storefront_support_live_contract import (
    SupportLiveAvailabilityResponse,
    SupportLiveEndRequest,
    SupportLiveMessageCreateRequest,
    SupportLiveSessionCreateRequest,
    SupportLiveSessionResponse,
)
from app.domains.support.services.storefront_support_live_service import (
    SupportLiveAuthError,
    SupportLiveConflictError,
    SupportLiveNotFoundError,
    SupportLiveValidationError,
    add_support_live_message,
    create_support_live_session,
    end_support_live_session,
    get_support_live_availability,
    get_support_live_session,
)

router = APIRouter(prefix="/support/live", tags=["support-live"])
SessionDep = Annotated[Session, Depends(get_session)]


def _extract_optional_access_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None

    if not authorization.startswith("Bearer "):
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


def _raise_live_http_error(exc: Exception) -> None:
    if isinstance(exc, SupportLiveValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SupportLiveAuthError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SupportLiveNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SupportLiveConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("/availability", response_model=SupportLiveAvailabilityResponse)
def support_live_availability(session: SessionDep) -> SupportLiveAvailabilityResponse:
    return get_support_live_availability(session)


@router.post(
    "/sessions",
    response_model=SupportLiveSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def support_live_sessions_create(
    payload: SupportLiveSessionCreateRequest,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportLiveSessionResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return create_support_live_session(session, access_token, payload)
    except (
        SupportLiveAuthError,
        SupportLiveConflictError,
        SupportLiveNotFoundError,
        SupportLiveValidationError,
    ) as exc:
        _raise_live_http_error(exc)
        raise


@router.get("/sessions/{session_code}", response_model=SupportLiveSessionResponse)
def support_live_session_detail(
    session_code: str,
    session: SessionDep,
    session_token: Annotated[str | None, Query(min_length=16, max_length=256)] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportLiveSessionResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return get_support_live_session(session, access_token, session_code, session_token)
    except (
        SupportLiveAuthError,
        SupportLiveConflictError,
        SupportLiveNotFoundError,
        SupportLiveValidationError,
    ) as exc:
        _raise_live_http_error(exc)
        raise


@router.post("/sessions/{session_code}/messages", response_model=SupportLiveSessionResponse)
def support_live_session_messages_create(
    session_code: str,
    payload: SupportLiveMessageCreateRequest,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportLiveSessionResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return add_support_live_message(session, access_token, session_code, payload)
    except (
        SupportLiveAuthError,
        SupportLiveConflictError,
        SupportLiveNotFoundError,
        SupportLiveValidationError,
    ) as exc:
        _raise_live_http_error(exc)
        raise


@router.post("/sessions/{session_code}/end", response_model=SupportLiveSessionResponse)
def support_live_session_end(
    session_code: str,
    payload: SupportLiveEndRequest,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportLiveSessionResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return end_support_live_session(session, access_token, session_code, payload)
    except (
        SupportLiveAuthError,
        SupportLiveConflictError,
        SupportLiveNotFoundError,
        SupportLiveValidationError,
    ) as exc:
        _raise_live_http_error(exc)
        raise
