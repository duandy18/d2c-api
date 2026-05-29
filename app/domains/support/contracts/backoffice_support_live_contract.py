"""Backoffice live support API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

BackofficeSupportPresenceStatus = Literal["online", "away", "offline"]
BackofficeSupportLiveSessionStatus = Literal["waiting", "active", "ended", "missed"]


class BackofficeSupportAgentPresenceUpdateRequest(BaseModel):
    presence_status: BackofficeSupportPresenceStatus
    max_active_sessions: int = Field(default=3, ge=1, le=20)


class BackofficeSupportAgentPresenceResponse(BaseModel):
    agent_code: str
    display_name: str
    presence_status: BackofficeSupportPresenceStatus
    max_active_sessions: int
    active_session_count: int
    last_heartbeat_at: datetime | None
    updated_at: datetime


class BackofficeSupportLiveMessageCreateRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)


class BackofficeSupportLiveEndRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class BackofficeSupportLiveMessage(BaseModel):
    message_code: str
    sender_type: str
    agent_code: str | None
    body: str
    created_at: datetime


class BackofficeSupportLiveSessionSummary(BaseModel):
    session_code: str
    conversation_code: str
    customer_id: int | None
    anonymous_id: str | None
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    status: BackofficeSupportLiveSessionStatus
    assigned_agent_code: str | None
    assigned_agent_name: str | None
    started_at: datetime
    accepted_at: datetime | None
    ended_at: datetime | None
    last_customer_seen_at: datetime | None
    last_agent_seen_at: datetime | None
    last_message_at: datetime | None


class BackofficeSupportLiveSessionsResponse(BaseModel):
    sessions: list[BackofficeSupportLiveSessionSummary] = Field(default_factory=list)
    count: int = Field(..., ge=0)


class BackofficeSupportLiveSessionResponse(BackofficeSupportLiveSessionSummary):
    messages: list[BackofficeSupportLiveMessage] = Field(default_factory=list)


class BackofficeSupportLivePresenceListResponse(BaseModel):
    agents: list[BackofficeSupportAgentPresenceResponse] = Field(default_factory=list)
    count: int = Field(..., ge=0)
