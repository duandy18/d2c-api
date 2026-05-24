"""Promotion checkout repositories."""

from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.domains.promotions.models.promotion import CustomerCoupon
from app.domains.published.models.published import PublishedCoupon, PublishedPromotion

PublishedCouponPromotion = tuple[PublishedCoupon, PublishedPromotion]


def get_best_active_all_store_percentage_promotion(
    session: Session,
    *,
    currency: str,
    subtotal_cents: int,
    now: datetime,
) -> PublishedPromotion | None:
    statement = (
        select(PublishedPromotion)
        .where(PublishedPromotion.is_active.is_(True))
        .where(PublishedPromotion.scope_type == "all_store")
        .where(PublishedPromotion.discount_type == "percentage")
        .where(PublishedPromotion.currency == currency)
        .where(
            or_(
                PublishedPromotion.starts_at.is_(None),
                PublishedPromotion.starts_at <= now,
            )
        )
        .where(
            or_(
                PublishedPromotion.ends_at.is_(None),
                PublishedPromotion.ends_at > now,
            )
        )
        .where(
            or_(
                PublishedPromotion.min_order_amount_cents.is_(None),
                PublishedPromotion.min_order_amount_cents <= subtotal_cents,
            )
        )
        .order_by(
            PublishedPromotion.published_at.desc(),
            PublishedPromotion.priority,
            PublishedPromotion.id,
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
        select(PublishedCoupon, PublishedPromotion)
        .join(
            PublishedPromotion,
            and_(
                PublishedPromotion.publish_version == PublishedCoupon.publish_version,
                PublishedPromotion.promotion_code == PublishedCoupon.promotion_code,
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
        .where(PublishedPromotion.is_active.is_(True))
        .where(PublishedPromotion.scope_type == "all_store")
        .where(PublishedPromotion.discount_type == "percentage")
        .where(PublishedPromotion.currency == currency)
        .where(
            or_(
                PublishedPromotion.starts_at.is_(None),
                PublishedPromotion.starts_at <= now,
            )
        )
        .where(
            or_(
                PublishedPromotion.ends_at.is_(None),
                PublishedPromotion.ends_at > now,
            )
        )
        .where(
            or_(
                PublishedPromotion.min_order_amount_cents.is_(None),
                PublishedPromotion.min_order_amount_cents <= subtotal_cents,
            )
        )
        .order_by(
            PublishedCoupon.published_at.desc(),
            PublishedPromotion.priority,
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
