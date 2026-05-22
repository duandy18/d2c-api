"""Promotion checkout repositories."""

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domains.promotions.models.promotion import Coupon, Promotion


def get_best_active_all_store_percentage_promotion(
    session: Session,
    *,
    currency: str,
    subtotal_cents: int,
    now: datetime,
) -> Promotion | None:
    statement = (
        select(Promotion)
        .where(Promotion.is_active.is_(True))
        .where(Promotion.status == "active")
        .where(Promotion.scope_type == "all_store")
        .where(Promotion.discount_type == "percentage")
        .where(Promotion.currency == currency)
        .where(
            or_(
                Promotion.starts_at.is_(None),
                Promotion.starts_at <= now,
            )
        )
        .where(
            or_(
                Promotion.ends_at.is_(None),
                Promotion.ends_at > now,
            )
        )
        .where(
            or_(
                Promotion.min_order_amount_cents.is_(None),
                Promotion.min_order_amount_cents <= subtotal_cents,
            )
        )
        .order_by(Promotion.priority, Promotion.id)
    )
    return session.scalar(statement)


def get_active_public_coupon_promotion_by_code(
    session: Session,
    *,
    coupon_code: str,
    currency: str,
    subtotal_cents: int,
    now: datetime,
) -> tuple[Coupon, Promotion] | None:
    statement = (
        select(Coupon, Promotion)
        .join(Promotion, Promotion.id == Coupon.promotion_id)
        .where(Coupon.coupon_code == coupon_code)
        .where(Coupon.is_active.is_(True))
        .where(Coupon.status == "active")
        .where(Coupon.coupon_type == "public_code")
        .where(
            or_(
                Coupon.starts_at.is_(None),
                Coupon.starts_at <= now,
            )
        )
        .where(
            or_(
                Coupon.ends_at.is_(None),
                Coupon.ends_at > now,
            )
        )
        .where(Promotion.is_active.is_(True))
        .where(Promotion.status == "active")
        .where(Promotion.scope_type == "all_store")
        .where(Promotion.discount_type == "percentage")
        .where(Promotion.currency == currency)
        .where(
            or_(
                Promotion.starts_at.is_(None),
                Promotion.starts_at <= now,
            )
        )
        .where(
            or_(
                Promotion.ends_at.is_(None),
                Promotion.ends_at > now,
            )
        )
        .where(
            or_(
                Promotion.min_order_amount_cents.is_(None),
                Promotion.min_order_amount_cents <= subtotal_cents,
            )
        )
        .order_by(Promotion.priority, Promotion.id)
    )
    return session.execute(statement).first()
