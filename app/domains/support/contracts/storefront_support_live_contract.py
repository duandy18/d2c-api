"""Storefront live support API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SupportLiveAvailabilityStatus = Literal["online", "offline"]
SupportLiveSessionStatus = Literal["waiting", "active", "ended", "missed"]
SupportLiveSenderType = Literal["customer", "agent", "system"]


class SupportLiveAvailabilityResponse(BaseModel):
    availability_status: SupportLiveAvailabilityStatus
    available_agent_count: int = Field(..., ge=0)
    waiting_session_count: int = Field(..., ge=0)
    active_session_count: int = Field(..., ge=0)
    message: str


class SupportLiveSessionCreateRequest(BaseModel):
    anonymous_id: str | None = Field(default=None, min_length=8, max_length=96)
    session_code: str | None = Field(default=None, min_length=8, max_length=96)
    contact_name: str | None = Field(default=None, max_length=120)
    contact_email: str | None = Field(default=None, min_length=3, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=32)
    opening_message: str = Field(..., min_length=1, max_length=5000)


class SupportLiveMessageCreateRequest(BaseModel):
    session_token: str | None = Field(default=None, min_length=16, max_length=256)
    body: str = Field(..., min_length=1, max_length=5000)


class SupportLiveEndRequest(BaseModel):
    session_token: str | None = Field(default=None, min_length=16, max_length=256)
    reason: str | None = Field(default=None, max_length=500)


class SupportLiveAgentSummary(BaseModel):
    agent_code: str
    display_name: str


class SupportLiveMessageResponse(BaseModel):
    message_code: str
    sender_type: SupportLiveSenderType
    agent_code: str | None = None
    body: str
    created_at: datetime


class SupportLiveSessionResponse(BaseModel):
    session_code: str
    session_token: str | None = None
    conversation_code: str
    status: SupportLiveSessionStatus
    assigned_agent: SupportLiveAgentSummary | None = None
    started_at: datetime
    accepted_at: datetime | None
    ended_at: datetime | None
    last_message_at: datetime | None
    messages: list[SupportLiveMessageResponse] = Field(default_factory=list)
