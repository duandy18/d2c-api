"""Analytics domain repositories."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.analytics.models.analytics import BehaviorEvent, VisitorSession


def get_visitor_session_by_code(
    session: Session,
    session_code: str,
) -> VisitorSession | None:
    statement = select(VisitorSession).where(VisitorSession.session_code == session_code)
    return session.scalar(statement)


def create_visitor_session(
    session: Session,
    visitor_session: VisitorSession,
) -> VisitorSession:
    session.add(visitor_session)
    session.flush()
    return visitor_session


def create_behavior_event(
    session: Session,
    behavior_event: BehaviorEvent,
) -> BehaviorEvent:
    session.add(behavior_event)
    session.flush()
    return behavior_event
