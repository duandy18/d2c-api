"""Storefront customer support API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

SupportTopic = Literal[
    "order_status",
    "shipping",
    "returns_after_sales",
    "product_question",
    "payment_issue",
    "other",
]
SupportStatus = Literal["open", "pending_agent", "pending_customer", "closed"]
SupportSenderType = Literal["customer", "agent", "system"]
SupportVisibility = Literal["public"]


class SupportConversationCreateRequest(BaseModel):
    anonymous_id: str | None = Field(default=None, min_length=8, max_length=96)
    session_code: str | None = Field(default=None, min_length=8, max_length=96)
    contact_name: str | None = Field(default=None, max_length=120)
    contact_email: str | None = Field(default=None, min_length=3, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=32)
    topic: SupportTopic
    related_order_no: str | None = Field(default=None, max_length=32)
    message: str = Field(..., min_length=1, max_length=5000)


class SupportMessageCreateRequest(BaseModel):
    conversation_token: str | None = Field(default=None, min_length=16, max_length=256)
    body: str = Field(..., min_length=1, max_length=5000)


class SupportMessageResponse(BaseModel):
    message_code: str
    sender_type: SupportSenderType
    body: str
    visibility: SupportVisibility
    created_at: datetime


class SupportConversationSummary(BaseModel):
    conversation_code: str
    topic: SupportTopic
    related_order_no: str | None
    status: SupportStatus
    source: str
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    message_count: int = Field(..., ge=0)
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class SupportConversationListResponse(BaseModel):
    conversations: list[SupportConversationSummary] = Field(default_factory=list)
    count: int = Field(..., ge=0)


class SupportConversationResponse(BaseModel):
    conversation_code: str
    topic: SupportTopic
    related_order_no: str | None
    status: SupportStatus
    source: str
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    conversation_token: str | None = None
    messages: list[SupportMessageResponse] = Field(default_factory=list)


class SupportConversationTokenQuery(BaseModel):
    conversation_token: str | None = Field(default=None, min_length=16, max_length=256)

    @model_validator(mode="after")
    def normalize_blank_token(self) -> SupportConversationTokenQuery:
        if self.conversation_token is not None and not self.conversation_token.strip():
            self.conversation_token = None
        return self
