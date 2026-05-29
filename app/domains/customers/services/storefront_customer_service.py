"""Storefront customer service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.domains.customers.contracts.storefront_customer_contract import (
    CustomerAuthResponse,
    CustomerLoginRequest,
    CustomerLogoutResponse,
    CustomerProfile,
    CustomerRegisterRequest,
)
from app.domains.customers.models.customer import (
    Customer,
    CustomerPasswordCredential,
    CustomerSession,
)
from app.domains.customers.repos.customer_repo import (
    create_customer,
    create_customer_session,
    create_password_credential,
    get_active_customer_by_session_token_hash,
    get_active_customer_session_by_token_hash,
    get_customer_by_email,
    get_customer_by_phone,
    get_password_credential,
    revoke_customer_session,
)
from app.security.passwords import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)

SESSION_TTL_HOURS = 24


class CustomerConflictError(Exception):
    pass


class CustomerAuthError(Exception):
    pass


def normalize_email(email: str | None) -> str | None:
    if email is None:
        return None

    normalized_email = email.strip().lower()
    return normalized_email or None


def normalize_phone(phone: str | None) -> str | None:
    if phone is None:
        return None

    normalized_phone = phone.strip()
    return normalized_phone or None


def build_customer_profile(customer: Customer) -> CustomerProfile:
    return CustomerProfile(
        customer_code=customer.customer_code,
        email=customer.email,
        phone=customer.phone,
        display_name=customer.display_name,
        status=customer.status,
        registered_at=customer.registered_at,
        last_login_at=customer.last_login_at,
    )


def register_customer(
    session: Session,
    payload: CustomerRegisterRequest,
) -> CustomerAuthResponse:
    email = normalize_email(payload.email)
    phone = normalize_phone(payload.phone)

    if email is None and phone is None:
        raise CustomerConflictError("customer_email_or_phone_required")

    if email is not None and get_customer_by_email(session, email) is not None:
        raise CustomerConflictError("customer_email_already_registered")

    if phone is not None and get_customer_by_phone(session, phone) is not None:
        raise CustomerConflictError("customer_phone_already_registered")

    now = datetime.now(UTC)
    customer = create_customer(
        session,
        Customer(
            customer_code=f"CUST-{uuid4().hex[:12].upper()}",
            email=email,
            phone=phone,
            display_name=payload.display_name,
            status="active",
            registered_at=now,
        ),
    )
    create_password_credential(
        session,
        CustomerPasswordCredential(
            customer_id=customer.id,
            password_hash=hash_password(payload.password),
            password_updated_at=now,
        ),
    )

    access_token, expires_at = create_login_session(session, customer)
    session.commit()

    return CustomerAuthResponse(
        access_token=access_token,
        expires_at=expires_at,
        customer=build_customer_profile(customer),
    )


def login_customer(
    session: Session,
    payload: CustomerLoginRequest,
) -> CustomerAuthResponse:
    email = normalize_email(payload.email)
    phone = normalize_phone(payload.phone)

    if email is not None:
        customer = get_customer_by_email(session, email)
    elif phone is not None:
        customer = get_customer_by_phone(session, phone)
    else:
        customer = None

    if customer is None or customer.status != "active":
        raise CustomerAuthError("invalid_customer_credentials")

    credential = get_password_credential(session, customer.id)

    if credential is None or not verify_password(payload.password, credential.password_hash):
        if credential is not None:
            credential.failed_login_count += 1
            session.commit()
        raise CustomerAuthError("invalid_customer_credentials")

    now = datetime.now(UTC)
    credential.failed_login_count = 0
    customer.last_login_at = now

    access_token, expires_at = create_login_session(session, customer)
    session.commit()

    return CustomerAuthResponse(
        access_token=access_token,
        expires_at=expires_at,
        customer=build_customer_profile(customer),
    )


def create_login_session(session: Session, customer: Customer) -> tuple[str, datetime]:
    access_token = generate_session_token()
    expires_at = datetime.now(UTC) + timedelta(hours=SESSION_TTL_HOURS)

    create_customer_session(
        session,
        CustomerSession(
            customer_id=customer.id,
            session_token_hash=hash_session_token(access_token),
            expires_at=expires_at,
        ),
    )

    return access_token, expires_at



def get_current_customer(
    session: Session,
    access_token: str,
) -> CustomerProfile:
    customer = get_active_customer_by_session_token_hash(
        session,
        hash_session_token(access_token),
        datetime.now(UTC),
    )

    if customer is None:
        raise CustomerAuthError("customer_auth_required")

    return build_customer_profile(customer)


def logout_customer(
    session: Session,
    access_token: str,
) -> CustomerLogoutResponse:
    now = datetime.now(UTC)
    customer_session = get_active_customer_session_by_token_hash(
        session,
        hash_session_token(access_token),
        now,
    )

    if customer_session is None:
        raise CustomerAuthError("customer_auth_required")

    revoke_customer_session(session, customer_session, now)
    session.commit()

    return CustomerLogoutResponse()
