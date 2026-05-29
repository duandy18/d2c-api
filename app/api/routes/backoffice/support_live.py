"""Backoffice live support routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.support.contracts.backoffice_support_live_contract import (
    BackofficeSupportAgentPresenceResponse,
    BackofficeSupportAgentPresenceUpdateRequest,
    BackofficeSupportLiveEndRequest,
    BackofficeSupportLiveMessageCreateRequest,
    BackofficeSupportLivePresenceListResponse,
    BackofficeSupportLiveSessionResponse,
    BackofficeSupportLiveSessionsResponse,
)
from app.domains.support.services.backoffice_support_live_service import (
    accept_backoffice_support_live_session,
    add_backoffice_support_live_message,
    end_backoffice_support_live_session,
    get_backoffice_support_live_session,
    list_backoffice_support_agent_presence,
    list_backoffice_support_live_sessions,
    update_backoffice_support_agent_presence,
)
from app.domains.support.services.backoffice_support_service import (
    BackofficeSupportAuthError,
    BackofficeSupportConflictError,
    BackofficeSupportNotFoundError,
    BackofficeSupportValidationError,
)

router = APIRouter(prefix="/backoffice/support", tags=["backoffice-support-live"])
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


@router.get("/agents/presence", response_model=BackofficeSupportLivePresenceListResponse)
def backoffice_support_agent_presence_list(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSupportLivePresenceListResponse:
    return list_backoffice_support_agent_presence(session)


@router.post(
    "/agents/{agent_code}/presence",
    response_model=BackofficeSupportAgentPresenceResponse,
)
def backoffice_support_agent_presence_update(
    agent_code: str,
    payload: BackofficeSupportAgentPresenceUpdateRequest,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSupportAgentPresenceResponse:
    try:
        return update_backoffice_support_agent_presence(session, agent_code, payload)
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.get("/live/sessions", response_model=BackofficeSupportLiveSessionsResponse)
def backoffice_support_live_sessions_list(
    _: BackofficeClientDep,
    session: SessionDep,
    status_filter: Annotated[
        str | None,
        Query(alias="status", pattern="^(waiting|active|ended|missed)$"),
    ] = None,
    assigned_agent_code: Annotated[str | None, Query(max_length=64)] = None,
) -> BackofficeSupportLiveSessionsResponse:
    return list_backoffice_support_live_sessions(
        session,
        status_filter=status_filter,
        assigned_agent_code=assigned_agent_code,
    )


@router.get("/live/sessions/{session_code}", response_model=BackofficeSupportLiveSessionResponse)
def backoffice_support_live_session_detail(
    session_code: str,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSupportLiveSessionResponse:
    try:
        return get_backoffice_support_live_session(session, session_code)
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.post(
    "/live/sessions/{session_code}/accept", response_model=BackofficeSupportLiveSessionResponse
)
def backoffice_support_live_session_accept(
    session_code: str,
    _: BackofficeClientDep,
    session: SessionDep,
    x_support_agent_code: Annotated[str | None, Header(alias="X-Support-Agent-Code")] = None,
) -> BackofficeSupportLiveSessionResponse:
    try:
        return accept_backoffice_support_live_session(session, session_code, x_support_agent_code)
    except (
        BackofficeSupportAuthError,
        BackofficeSupportConflictError,
        BackofficeSupportNotFoundError,
        BackofficeSupportValidationError,
    ) as exc:
        _raise_http_error(exc)
        raise


@router.post(
    "/live/sessions/{session_code}/messages", response_model=BackofficeSupportLiveSessionResponse
)
def backoffice_support_live_session_messages_create(
    session_code: str,
    payload: BackofficeSupportLiveMessageCreateRequest,
    _: BackofficeClientDep,
    session: SessionDep,
    x_support_agent_code: Annotated[str | None, Header(alias="X-Support-Agent-Code")] = None,
) -> BackofficeSupportLiveSessionResponse:
    try:
        return add_backoffice_support_live_message(
            session,
            session_code,
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
    "/live/sessions/{session_code}/end", response_model=BackofficeSupportLiveSessionResponse
)
def backoffice_support_live_session_end(
    session_code: str,
    payload: BackofficeSupportLiveEndRequest,
    _: BackofficeClientDep,
    session: SessionDep,
    x_support_agent_code: Annotated[str | None, Header(alias="X-Support-Agent-Code")] = None,
) -> BackofficeSupportLiveSessionResponse:
    try:
        return end_backoffice_support_live_session(
            session,
            session_code,
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
