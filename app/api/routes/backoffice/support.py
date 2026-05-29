"""Backoffice support workbench routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.support.contracts.backoffice_support_contract import (
    BackofficeSupportAgent,
    BackofficeSupportAgentCreateRequest,
    BackofficeSupportAgentsResponse,
    BackofficeSupportAssignRequest,
    BackofficeSupportCloseRequest,
    BackofficeSupportConversationListResponse,
    BackofficeSupportConversationResponse,
    BackofficeSupportEventsResponse,
    BackofficeSupportMessageCreateRequest,
)
from app.domains.support.services.backoffice_support_service import (
    BackofficeSupportAuthError,
    BackofficeSupportConflictError,
    BackofficeSupportNotFoundError,
    BackofficeSupportValidationError,
    add_backoffice_support_message,
    assign_backoffice_support_conversation,
    close_backoffice_support_conversation,
    create_backoffice_support_agent,
    get_backoffice_support_conversation,
    list_backoffice_support_agents,
    list_backoffice_support_conversations,
    list_backoffice_support_events,
)

router = APIRouter(prefix="/backoffice/support", tags=["backoffice-support"])
SessionDep = Annotated[Session, Depends(get_session)]


def require_backoffice_client(
    x_backoffice_client: Annotated[str | None, Header(alias="X-Backoffice-Client")] = None,
) -> None:
    if x_backoffice_client != "d2c-backoffice":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="backoffice_client_required",
        )


BackofficeClientDep = Annotated[None, Depends(require_backoffice_client)]


def _raise_http_error(exc: Exception) -> None:
    if isinstance(exc, BackofficeSupportAuthError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    if isinstance(exc, BackofficeSupportValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    if isinstance(exc, BackofficeSupportNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, BackofficeSupportConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    raise exc


@router.get("/health")
def backoffice_support_health(_: BackofficeClientDep) -> dict[str, str]:
    return {
        "status": "ok",
        "module": "support",
        "workbench": "d2c_support_workbench",
    }


@router.get("/agents", response_model=BackofficeSupportAgentsResponse)
def backoffice_support_agents_list(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSupportAgentsResponse:
    return list_backoffice_support_agents(session)


@router.post(
    "/agents",
    response_model=BackofficeSupportAgent,
    status_code=status.HTTP_201_CREATED,
)
def backoffice_support_agents_create(
    payload: BackofficeSupportAgentCreateRequest,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSupportAgent:
    try:
        return create_backoffice_support_agent(session, payload)
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.get("/conversations", response_model=BackofficeSupportConversationListResponse)
def backoffice_support_conversations_list(
    _: BackofficeClientDep,
    session: SessionDep,
    status_filter: Annotated[
        str | None,
        Query(alias="status", pattern="^(open|pending_agent|pending_customer|closed)$"),
    ] = None,
    topic: Annotated[
        str | None,
        Query(
            pattern=(
                "^(order_status|shipping|returns_after_sales|product_question|payment_issue|other)$"
            )
        ),
    ] = None,
    assigned_agent_code: Annotated[str | None, Query(max_length=64)] = None,
) -> BackofficeSupportConversationListResponse:
    return list_backoffice_support_conversations(
        session,
        status_filter=status_filter,
        topic=topic,
        assigned_agent_code=assigned_agent_code,
    )


@router.get(
    "/conversations/{conversation_code}",
    response_model=BackofficeSupportConversationResponse,
)
def backoffice_support_conversation_detail(
    conversation_code: str,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSupportConversationResponse:
    try:
        return get_backoffice_support_conversation(session, conversation_code)
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.post(
    "/conversations/{conversation_code}/assign",
    response_model=BackofficeSupportConversationResponse,
)
def backoffice_support_conversation_assign(
    conversation_code: str,
    payload: BackofficeSupportAssignRequest,
    _: BackofficeClientDep,
    session: SessionDep,
    x_support_agent_code: Annotated[str | None, Header(alias="X-Support-Agent-Code")] = None,
) -> BackofficeSupportConversationResponse:
    try:
        return assign_backoffice_support_conversation(
            session,
            conversation_code,
            x_support_agent_code,
            payload,
        )
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.post(
    "/conversations/{conversation_code}/messages",
    response_model=BackofficeSupportConversationResponse,
)
def backoffice_support_conversation_messages_create(
    conversation_code: str,
    payload: BackofficeSupportMessageCreateRequest,
    _: BackofficeClientDep,
    session: SessionDep,
    x_support_agent_code: Annotated[str | None, Header(alias="X-Support-Agent-Code")] = None,
) -> BackofficeSupportConversationResponse:
    try:
        return add_backoffice_support_message(
            session,
            conversation_code,
            x_support_agent_code,
            payload,
        )
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.post(
    "/conversations/{conversation_code}/close",
    response_model=BackofficeSupportConversationResponse,
)
def backoffice_support_conversation_close(
    conversation_code: str,
    payload: BackofficeSupportCloseRequest,
    _: BackofficeClientDep,
    session: SessionDep,
    x_support_agent_code: Annotated[str | None, Header(alias="X-Support-Agent-Code")] = None,
) -> BackofficeSupportConversationResponse:
    try:
        return close_backoffice_support_conversation(
            session,
            conversation_code,
            x_support_agent_code,
            payload,
        )
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.get(
    "/conversations/{conversation_code}/events",
    response_model=BackofficeSupportEventsResponse,
)
def backoffice_support_conversation_events(
    conversation_code: str,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSupportEventsResponse:
    try:
        return list_backoffice_support_events(session, conversation_code)
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise
