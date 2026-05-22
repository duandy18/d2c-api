"""Backoffice promotion service."""

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.promotions.contracts.backoffice_promotion_contract import (
    BackofficeCoupon,
    BackofficeCouponsResponse,
    BackofficeCustomerCoupon,
    BackofficeCustomerCouponsResponse,
    BackofficePromotion,
    BackofficePromotionCreateRequest,
    BackofficePromotionsResponse,
    BackofficePromotionTarget,
    BackofficePromotionTargetsResponse,
)
from app.domains.promotions.models.promotion import (
    Coupon,
    CustomerCoupon,
    Promotion,
    PromotionTarget,
)
from app.domains.promotions.repos.backoffice_promotion_repo import (
    create_promotion,
    create_promotion_target,
    get_promotion_by_code,
    list_coupon_rows,
    list_customer_coupon_rows,
    list_promotion_target_rows,
    list_promotions,
)


class BackofficePromotionDuplicateCodeError(Exception):
    pass


class BackofficePromotionInvalidRangeError(Exception):
    pass


class BackofficePromotionNotFoundError(Exception):
    pass


def _build_promotion(promotion: Promotion) -> BackofficePromotion:
    return BackofficePromotion(
        id=promotion.id,
        promotion_code=promotion.promotion_code,
        name=promotion.name,
        description=promotion.description,
        promotion_type=promotion.promotion_type,
        discount_type=promotion.discount_type,
        discount_value=promotion.discount_value,
        scope_type=promotion.scope_type,
        min_order_amount_cents=promotion.min_order_amount_cents,
        max_discount_cents=promotion.max_discount_cents,
        currency=promotion.currency,
        starts_at=promotion.starts_at,
        ends_at=promotion.ends_at,
        status=promotion.status,
        priority=promotion.priority,
        stackable=promotion.stackable,
        is_active=promotion.is_active,
        created_at=promotion.created_at,
        updated_at=promotion.updated_at,
    )


def get_backoffice_promotions(session: Session) -> BackofficePromotionsResponse:
    promotions = [_build_promotion(promotion) for promotion in list_promotions(session)]
    return BackofficePromotionsResponse(count=len(promotions), promotions=promotions)


def create_backoffice_promotion(
    session: Session,
    payload: BackofficePromotionCreateRequest,
) -> BackofficePromotion:
    if (
        payload.ends_at is not None
        and payload.starts_at is not None
        and payload.ends_at <= payload.starts_at
    ):
        raise BackofficePromotionInvalidRangeError("promotion_effective_range_invalid")

    if get_promotion_by_code(session, payload.promotion_code) is not None:
        raise BackofficePromotionDuplicateCodeError("promotion_code_already_exists")

    promotion = Promotion(
        promotion_code=payload.promotion_code,
        name=payload.name,
        description=payload.description,
        promotion_type=payload.promotion_type,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        scope_type=payload.scope_type,
        min_order_amount_cents=payload.min_order_amount_cents,
        max_discount_cents=payload.max_discount_cents,
        currency=payload.currency.upper(),
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        status="draft",
        priority=payload.priority,
        stackable=payload.stackable,
        is_active=False,
    )

    try:
        create_promotion(session, promotion)
        create_promotion_target(
            session,
            PromotionTarget(
                promotion_id=promotion.id,
                target_type="all_store",
                target_id=None,
                target_code=None,
            ),
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise BackofficePromotionDuplicateCodeError("promotion_code_already_exists") from exc

    return _build_promotion(promotion)


def activate_backoffice_promotion(
    session: Session,
    promotion_code: str,
) -> BackofficePromotion:
    promotion = get_promotion_by_code(session, promotion_code)

    if promotion is None:
        raise BackofficePromotionNotFoundError("promotion_not_found")

    now = datetime.now(UTC)
    promotion.status = "active"
    promotion.is_active = True
    promotion.updated_at = now
    session.commit()

    return _build_promotion(promotion)


def deactivate_backoffice_promotion(
    session: Session,
    promotion_code: str,
) -> BackofficePromotion:
    promotion = get_promotion_by_code(session, promotion_code)

    if promotion is None:
        raise BackofficePromotionNotFoundError("promotion_not_found")

    now = datetime.now(UTC)
    promotion.status = "paused"
    promotion.is_active = False
    promotion.updated_at = now
    session.commit()

    return _build_promotion(promotion)


def _build_promotion_target(
    target: PromotionTarget,
    promotion: Promotion,
) -> BackofficePromotionTarget:
    return BackofficePromotionTarget(
        id=target.id,
        promotion_id=target.promotion_id,
        promotion_code=promotion.promotion_code,
        target_type=target.target_type,
        target_id=target.target_id,
        target_code=target.target_code,
        created_at=target.created_at,
    )


def get_backoffice_promotion_targets(session: Session) -> BackofficePromotionTargetsResponse:
    targets = [
        _build_promotion_target(target, promotion)
        for target, promotion in list_promotion_target_rows(session)
    ]
    return BackofficePromotionTargetsResponse(
        count=len(targets),
        promotion_targets=targets,
    )


def _build_coupon(coupon: Coupon, promotion: Promotion) -> BackofficeCoupon:
    return BackofficeCoupon(
        id=coupon.id,
        coupon_code=coupon.coupon_code,
        name=coupon.name,
        promotion_id=coupon.promotion_id,
        promotion_code=promotion.promotion_code,
        coupon_type=coupon.coupon_type,
        total_limit=coupon.total_limit,
        per_customer_limit=coupon.per_customer_limit,
        starts_at=coupon.starts_at,
        ends_at=coupon.ends_at,
        status=coupon.status,
        is_active=coupon.is_active,
        created_at=coupon.created_at,
        updated_at=coupon.updated_at,
    )


def get_backoffice_coupons(session: Session) -> BackofficeCouponsResponse:
    coupons = [_build_coupon(coupon, promotion) for coupon, promotion in list_coupon_rows(session)]
    return BackofficeCouponsResponse(count=len(coupons), coupons=coupons)


def _build_customer_coupon(
    customer_coupon: CustomerCoupon,
    coupon: Coupon,
    promotion: Promotion,
) -> BackofficeCustomerCoupon:
    return BackofficeCustomerCoupon(
        id=customer_coupon.id,
        customer_coupon_code=customer_coupon.customer_coupon_code,
        coupon_id=customer_coupon.coupon_id,
        coupon_code=coupon.coupon_code,
        promotion_id=coupon.promotion_id,
        promotion_code=promotion.promotion_code,
        customer_id=customer_coupon.customer_id,
        status=customer_coupon.status,
        claimed_at=customer_coupon.claimed_at,
        used_at=customer_coupon.used_at,
        order_id=customer_coupon.order_id,
        created_at=customer_coupon.created_at,
        updated_at=customer_coupon.updated_at,
    )


def get_backoffice_customer_coupons(session: Session) -> BackofficeCustomerCouponsResponse:
    customer_coupons = [
        _build_customer_coupon(customer_coupon, coupon, promotion)
        for customer_coupon, coupon, promotion in list_customer_coupon_rows(session)
    ]
    return BackofficeCustomerCouponsResponse(
        count=len(customer_coupons),
        customer_coupons=customer_coupons,
    )
