from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.analytics import BehaviorEvent, VisitorSession
from app.repos.analytics_repo import (
    create_behavior_event,
    create_visitor_session,
    get_visitor_session_by_code,
)
from app.schemas.analytics import BehaviorEventRequest, BehaviorEventResponse


def record_behavior_event(
    session: Session,
    payload: BehaviorEventRequest,
    user_agent: str | None,
) -> BehaviorEventResponse:
    occurred_at = payload.occurred_at or datetime.now(UTC)

    visitor_session = get_visitor_session_by_code(session, payload.session_code)

    if visitor_session is None:
        visitor_session = create_visitor_session(
            session,
            VisitorSession(
                session_code=payload.session_code,
                anonymous_id=payload.anonymous_id,
                last_seen_at=occurred_at,
                user_agent=user_agent,
                referrer=payload.referrer,
                utm_source=payload.utm_source,
                utm_medium=payload.utm_medium,
                utm_campaign=payload.utm_campaign,
            ),
        )
    else:
        visitor_session.last_seen_at = occurred_at
        if user_agent and not visitor_session.user_agent:
            visitor_session.user_agent = user_agent
        if payload.referrer and not visitor_session.referrer:
            visitor_session.referrer = payload.referrer
        if payload.utm_source and not visitor_session.utm_source:
            visitor_session.utm_source = payload.utm_source
        if payload.utm_medium and not visitor_session.utm_medium:
            visitor_session.utm_medium = payload.utm_medium
        if payload.utm_campaign and not visitor_session.utm_campaign:
            visitor_session.utm_campaign = payload.utm_campaign

    event_code = f"EVT-{uuid4().hex[:16].upper()}"
    create_behavior_event(
        session,
        BehaviorEvent(
            event_code=event_code,
            session_id=visitor_session.id,
            anonymous_id=payload.anonymous_id,
            customer_id=visitor_session.customer_id,
            event_type=payload.event_type,
            page_path=payload.page_path,
            product_code=payload.product_code,
            sku_code=payload.sku_code,
            duration_ms=payload.duration_ms,
            event_metadata=payload.metadata,
            occurred_at=occurred_at,
        ),
    )
    session.commit()

    return BehaviorEventResponse(
        event_code=event_code,
        session_code=payload.session_code,
        event_type=payload.event_type,
        occurred_at=occurred_at,
    )
