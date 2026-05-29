"""Storefront support routes; HTTP paths remain /support/*."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.support.contracts.storefront_support_contract import (
    SupportConversationCreateRequest,
    SupportConversationListResponse,
    SupportConversationResponse,
    SupportMessageCreateRequest,
)
from app.domains.support.services.storefront_support_service import (
    SupportAuthError,
    SupportConflictError,
    SupportNotFoundError,
    SupportValidationError,
    add_support_conversation_message,
    create_support_conversation,
    get_support_conversation,
    list_support_conversations,
)

router = APIRouter(prefix="/support", tags=["support"])
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


def _raise_support_http_error(exc: Exception) -> None:
    if isinstance(exc, SupportValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SupportAuthError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SupportNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SupportConflictError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("/health")
def support_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "support",
        "conversation_storage": "d2c_support_conversations",
        "message_storage": "d2c_support_messages",
    }


@router.post(
    "/conversations",
    response_model=SupportConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def support_conversations_create(
    payload: SupportConversationCreateRequest,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportConversationResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return create_support_conversation(session, access_token, payload)
    except (
        SupportAuthError,
        SupportValidationError,
        SupportNotFoundError,
        SupportConflictError,
    ) as exc:
        _raise_support_http_error(exc)
        raise


@router.get("/conversations", response_model=SupportConversationListResponse)
def support_conversations_list(
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportConversationListResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return list_support_conversations(session, access_token)
    except (
        SupportAuthError,
        SupportValidationError,
        SupportNotFoundError,
        SupportConflictError,
    ) as exc:
        _raise_support_http_error(exc)
        raise


@router.get(
    "/conversations/{conversation_code}",
    response_model=SupportConversationResponse,
)
def support_conversation_detail(
    conversation_code: str,
    session: SessionDep,
    conversation_token: Annotated[str | None, Query(min_length=16, max_length=256)] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportConversationResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return get_support_conversation(
            session,
            access_token,
            conversation_code,
            conversation_token,
        )
    except (
        SupportAuthError,
        SupportValidationError,
        SupportNotFoundError,
        SupportConflictError,
    ) as exc:
        _raise_support_http_error(exc)
        raise


@router.post(
    "/conversations/{conversation_code}/messages",
    response_model=SupportConversationResponse,
)
def support_conversation_messages_create(
    conversation_code: str,
    payload: SupportMessageCreateRequest,
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> SupportConversationResponse:
    access_token = _extract_optional_access_token(authorization)

    try:
        return add_support_conversation_message(
            session,
            access_token,
            conversation_code,
            payload,
        )
    except (
        SupportAuthError,
        SupportValidationError,
        SupportNotFoundError,
        SupportConflictError,
    ) as exc:
        _raise_support_http_error(exc)
        raise
