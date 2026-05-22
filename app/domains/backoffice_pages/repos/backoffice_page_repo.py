from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.backoffice_pages.models.backoffice_page import BackofficePage


def list_backoffice_pages(session: Session) -> list[BackofficePage]:
    statement = select(BackofficePage).order_by(
        BackofficePage.level,
        BackofficePage.sort_order,
        BackofficePage.page_code,
    )
    return list(session.scalars(statement).all())
