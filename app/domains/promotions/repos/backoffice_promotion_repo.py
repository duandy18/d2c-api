"""Backoffice promotion usage repositories retained in d2c-api."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.promotions.models.promotion import Coupon, CustomerCoupon, Promotion


def list_customer_coupon_rows(
    session: Session,
) -> list[tuple[CustomerCoupon, Coupon, Promotion]]:
    statement = (
        select(CustomerCoupon, Coupon, Promotion)
        .join(Coupon, Coupon.id == CustomerCoupon.coupon_id)
        .join(Promotion, Promotion.id == Coupon.promotion_id)
        .order_by(CustomerCoupon.id.desc())
    )
    return list(session.execute(statement).all())
