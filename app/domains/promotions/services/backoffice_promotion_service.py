"""Backoffice promotion usage service retained in d2c-api."""

from sqlalchemy.orm import Session

from app.domains.promotions.contracts.backoffice_promotion_contract import (
    BackofficeCustomerCoupon,
    BackofficeCustomerCouponsResponse,
)
from app.domains.promotions.models.promotion import CustomerCoupon
from app.domains.promotions.repos.backoffice_promotion_repo import list_customer_coupon_rows


def _build_customer_coupon(
    customer_coupon: CustomerCoupon,
) -> BackofficeCustomerCoupon:
    return BackofficeCustomerCoupon(
        id=customer_coupon.id,
        customer_coupon_code=customer_coupon.customer_coupon_code,
        publish_version=customer_coupon.publish_version,
        coupon_code=customer_coupon.coupon_code,
        coupon_name=customer_coupon.coupon_name,
        coupon_type=customer_coupon.coupon_type,
        promotion_code=customer_coupon.promotion_code,
        promotion_name=customer_coupon.promotion_name,
        promotion_type=customer_coupon.promotion_type,
        promotion_discount_type=customer_coupon.promotion_discount_type,
        promotion_discount_value=customer_coupon.promotion_discount_value,
        customer_id=customer_coupon.customer_id,
        status=customer_coupon.status,
        claimed_at=customer_coupon.claimed_at,
        used_at=customer_coupon.used_at,
        order_id=customer_coupon.order_id,
        order_no=customer_coupon.order_no,
        created_at=customer_coupon.created_at,
        updated_at=customer_coupon.updated_at,
    )


def get_backoffice_customer_coupons(session: Session) -> BackofficeCustomerCouponsResponse:
    customer_coupons = [
        _build_customer_coupon(customer_coupon)
        for customer_coupon in list_customer_coupon_rows(session)
    ]
    return BackofficeCustomerCouponsResponse(
        count=len(customer_coupons),
        customer_coupons=customer_coupons,
    )
