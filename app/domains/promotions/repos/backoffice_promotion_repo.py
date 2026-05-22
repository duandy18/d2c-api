"""Backoffice promotion repositories."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.promotions.models.promotion import (
    Coupon,
    CustomerCoupon,
    Promotion,
    PromotionTarget,
)


def get_promotion_by_code(
    session: Session,
    promotion_code: str,
) -> Promotion | None:
    statement = select(Promotion).where(Promotion.promotion_code == promotion_code)
    return session.scalar(statement)


def list_promotions(session: Session) -> list[Promotion]:
    statement = select(Promotion).order_by(
        Promotion.is_active.desc(),
        Promotion.status,
        Promotion.priority,
        Promotion.id.desc(),
    )
    return list(session.scalars(statement).all())


def create_promotion(
    session: Session,
    promotion: Promotion,
) -> Promotion:
    session.add(promotion)
    session.flush()
    return promotion


def create_promotion_target(
    session: Session,
    target: PromotionTarget,
) -> PromotionTarget:
    session.add(target)
    session.flush()
    return target


def get_coupon_by_code(
    session: Session,
    coupon_code: str,
) -> Coupon | None:
    statement = select(Coupon).where(Coupon.coupon_code == coupon_code)
    return session.scalar(statement)


def create_coupon(
    session: Session,
    coupon: Coupon,
) -> Coupon:
    session.add(coupon)
    session.flush()
    return coupon


def get_coupon_row_by_code(
    session: Session,
    coupon_code: str,
) -> tuple[Coupon, Promotion] | None:
    statement = (
        select(Coupon, Promotion)
        .join(Promotion, Promotion.id == Coupon.promotion_id)
        .where(Coupon.coupon_code == coupon_code)
    )
    return session.execute(statement).first()


def list_promotion_target_rows(
    session: Session,
) -> list[tuple[PromotionTarget, Promotion]]:
    statement = (
        select(PromotionTarget, Promotion)
        .join(Promotion, Promotion.id == PromotionTarget.promotion_id)
        .order_by(PromotionTarget.id.desc())
    )
    return list(session.execute(statement).all())


def list_coupon_rows(
    session: Session,
) -> list[tuple[Coupon, Promotion]]:
    statement = (
        select(Coupon, Promotion)
        .join(Promotion, Promotion.id == Coupon.promotion_id)
        .order_by(Coupon.id.desc())
    )
    return list(session.execute(statement).all())


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
