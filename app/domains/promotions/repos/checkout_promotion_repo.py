"""Promotion checkout repositories.

Checkout reads terminal published PromotionRule / PromotionTarget / Coupon
snapshots. Legacy d2c_published_promotions remains available only for old
published debug/read surfaces and is no longer part of checkout execution.
"""

from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.domains.promotions.models.promotion import CustomerCoupon
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishedPromotionRule,
    PublishedPromotionTarget,
)

PublishedCouponPromotion = tuple[PublishedCoupon, PublishedPromotionRule]


def _active_rule_filters(
    *,
    currency: str,
    subtotal_cents: int,
    now: datetime,
) -> tuple[object, ...]:
    return (
        PublishedPromotionRule.is_active.is_(True),
        PublishedPromotionRule.discount_type == "percentage",
        PublishedPromotionRule.currency == currency,
        or_(
            PublishedPromotionRule.starts_at.is_(None),
            PublishedPromotionRule.starts_at <= now,
        ),
        or_(
            PublishedPromotionRule.ends_at.is_(None),
            PublishedPromotionRule.ends_at > now,
        ),
        or_(
            PublishedPromotionRule.threshold_amount_cents.is_(None),
            PublishedPromotionRule.threshold_amount_cents <= subtotal_cents,
        ),
    )


def _all_store_target_filters() -> tuple[object, ...]:
    return (
        PublishedPromotionTarget.target_type == "all_store",
        PublishedPromotionTarget.target_code.is_(None),
        PublishedPromotionTarget.target_id.is_(None),
    )


def get_best_active_all_store_percentage_promotion(
    session: Session,
    *,
    currency: str,
    subtotal_cents: int,
    now: datetime,
) -> PublishedPromotionRule | None:
    statement = (
        select(PublishedPromotionRule)
        .join(
            PublishedPromotionTarget,
            and_(
                PublishedPromotionTarget.publish_version == PublishedPromotionRule.publish_version,
                PublishedPromotionTarget.promotion_code == PublishedPromotionRule.promotion_code,
            ),
        )
        .where(*_active_rule_filters(currency=currency, subtotal_cents=subtotal_cents, now=now))
        .where(*_all_store_target_filters())
        .order_by(
            PublishedPromotionRule.published_at.desc(),
            PublishedPromotionRule.priority,
            PublishedPromotionRule.id,
        )
        .limit(1)
    )
    return session.scalar(statement)


def get_active_public_coupon_promotion_by_code(
    session: Session,
    *,
    coupon_code: str,
    currency: str,
    subtotal_cents: int,
    now: datetime,
) -> PublishedCouponPromotion | None:
    statement = (
        select(PublishedCoupon, PublishedPromotionRule)
        .join(
            PublishedPromotionRule,
            and_(
                PublishedPromotionRule.publish_version == PublishedCoupon.publish_version,
                PublishedPromotionRule.promotion_code == PublishedCoupon.promotion_code,
            ),
        )
        .join(
            PublishedPromotionTarget,
            and_(
                PublishedPromotionTarget.publish_version == PublishedPromotionRule.publish_version,
                PublishedPromotionTarget.promotion_code == PublishedPromotionRule.promotion_code,
            ),
        )
        .where(PublishedCoupon.coupon_code == coupon_code)
        .where(PublishedCoupon.is_active.is_(True))
        .where(PublishedCoupon.coupon_type == "public_code")
        .where(
            or_(
                PublishedCoupon.starts_at.is_(None),
                PublishedCoupon.starts_at <= now,
            )
        )
        .where(
            or_(
                PublishedCoupon.ends_at.is_(None),
                PublishedCoupon.ends_at > now,
            )
        )
        .where(*_active_rule_filters(currency=currency, subtotal_cents=subtotal_cents, now=now))
        .where(*_all_store_target_filters())
        .order_by(
            PublishedCoupon.published_at.desc(),
            PublishedPromotionRule.priority,
            PublishedCoupon.id,
        )
        .limit(1)
    )
    return session.execute(statement).first()


def count_coupon_used(
    session: Session,
    coupon_code: str,
) -> int:
    statement = (
        select(func.count())
        .select_from(CustomerCoupon)
        .where(CustomerCoupon.coupon_code == coupon_code)
        .where(CustomerCoupon.status == "used")
        .where(CustomerCoupon.used_at.is_not(None))
    )
    return int(session.scalar(statement) or 0)


def count_customer_coupon_used(
    session: Session,
    *,
    coupon_code: str,
    customer_id: int,
) -> int:
    statement = (
        select(func.count())
        .select_from(CustomerCoupon)
        .where(CustomerCoupon.coupon_code == coupon_code)
        .where(CustomerCoupon.customer_id == customer_id)
        .where(CustomerCoupon.status == "used")
        .where(CustomerCoupon.used_at.is_not(None))
    )
    return int(session.scalar(statement) or 0)


def create_customer_coupon_usage(
    session: Session,
    customer_coupon: CustomerCoupon,
) -> CustomerCoupon:
    session.add(customer_coupon)
    session.flush()
    return customer_coupon
