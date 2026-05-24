"""Backoffice promotion usage service retained in d2c-api."""

from sqlalchemy.orm import Session

from app.domains.promotions.contracts.backoffice_promotion_contract import (
    BackofficeCustomerCoupon,
    BackofficeCustomerCouponsResponse,
)
from app.domains.promotions.models.promotion import Coupon, CustomerCoupon, Promotion
from app.domains.promotions.repos.backoffice_promotion_repo import list_customer_coupon_rows


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
