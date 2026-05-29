"""Backoffice support workbench API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

BackofficeSupportStatus = Literal["open", "pending_agent", "pending_customer", "closed"]
BackofficeSupportTopic = Literal[
    "order_status",
    "shipping",
    "returns_after_sales",
    "product_question",
    "payment_issue",
    "other",
]


class BackofficeSupportAgentCreateRequest(BaseModel):
    agent_code: str | None = Field(default=None, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=255)


class BackofficeSupportAgent(BaseModel):
    agent_code: str
    display_name: str
    email: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class BackofficeSupportAgentsResponse(BaseModel):
    agents: list[BackofficeSupportAgent] = Field(default_factory=list)
    count: int = Field(..., ge=0)


class BackofficeSupportMessageCreateRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)
    visibility: Literal["public", "internal"] = "public"


class BackofficeSupportAssignRequest(BaseModel):
    agent_code: str = Field(..., min_length=1, max_length=64)


class BackofficeSupportCloseRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class BackofficeSupportContact(BaseModel):
    contact_code: str
    customer_id: int | None
    anonymous_id: str | None
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    source: str
    first_seen_at: datetime
    last_seen_at: datetime


class BackofficeSupportMessage(BaseModel):
    message_code: str
    sender_type: str
    agent_code: str | None = None
    body: str
    visibility: str
    message_kind: str
    created_at: datetime


class BackofficeSupportConversationSummary(BaseModel):
    conversation_code: str
    customer_id: int | None
    contact: BackofficeSupportContact | None
    assigned_agent: BackofficeSupportAgent | None
    topic: BackofficeSupportTopic
    related_order_no: str | None
    status: BackofficeSupportStatus
    priority: str
    source: str
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    message_count: int = Field(..., ge=0)
    last_message_at: datetime | None
    last_customer_message_at: datetime | None
    last_agent_message_at: datetime | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class BackofficeSupportConversationListResponse(BaseModel):
    conversations: list[BackofficeSupportConversationSummary] = Field(default_factory=list)
    count: int = Field(..., ge=0)


class BackofficeSupportConversationResponse(BackofficeSupportConversationSummary):
    messages: list[BackofficeSupportMessage] = Field(default_factory=list)


class BackofficeSupportEvent(BaseModel):
    event_code: str
    event_type: str
    actor_type: str
    actor_agent_code: str | None
    message_code: str | None
    assignment_code: str | None
    from_status: str | None
    to_status: str | None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class BackofficeSupportEventsResponse(BaseModel):
    events: list[BackofficeSupportEvent] = Field(default_factory=list)
    count: int = Field(..., ge=0)
