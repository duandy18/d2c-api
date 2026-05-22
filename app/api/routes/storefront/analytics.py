"""Storefront analytics routes; HTTP paths remain /analytics/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.analytics.contracts.storefront_analytics_contract import (
    BehaviorEventRequest,
    BehaviorEventResponse,
)
from app.domains.analytics.services.storefront_analytics_service import record_behavior_event

router = APIRouter(prefix="/analytics", tags=["analytics"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/health")
def analytics_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "analytics",
        "event_sink": "d2c_behavior_events",
    }


@router.post(
    "/events",
    response_model=BehaviorEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def analytics_events(
    payload: BehaviorEventRequest,
    session: SessionDep,
    user_agent: Annotated[str | None, Header(alias="User-Agent")] = None,
) -> BehaviorEventResponse:
    return record_behavior_event(session, payload, user_agent)
