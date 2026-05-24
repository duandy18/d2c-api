"""Backoffice promotion usage repositories retained in d2c-api."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.promotions.models.promotion import CustomerCoupon


def list_customer_coupon_rows(
    session: Session,
) -> list[CustomerCoupon]:
    statement = select(CustomerCoupon).order_by(CustomerCoupon.id.desc())
    return list(session.scalars(statement).all())
