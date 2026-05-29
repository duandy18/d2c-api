"""Customer domain repositories."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.customers.models.customer import (
    Customer,
    CustomerPasswordCredential,
    CustomerSession,
)


def get_customer_by_email(session: Session, email: str) -> Customer | None:
    statement = select(Customer).where(Customer.email == email)
    return session.scalar(statement)


def get_customer_by_phone(session: Session, phone: str) -> Customer | None:
    statement = select(Customer).where(Customer.phone == phone)
    return session.scalar(statement)


def create_customer(session: Session, customer: Customer) -> Customer:
    session.add(customer)
    session.flush()
    return customer


def create_password_credential(
    session: Session,
    credential: CustomerPasswordCredential,
) -> CustomerPasswordCredential:
    session.add(credential)
    session.flush()
    return credential


def get_password_credential(
    session: Session,
    customer_id: int,
) -> CustomerPasswordCredential | None:
    statement = select(CustomerPasswordCredential).where(
        CustomerPasswordCredential.customer_id == customer_id
    )
    return session.scalar(statement)


def create_customer_session(
    session: Session,
    customer_session: CustomerSession,
) -> CustomerSession:
    session.add(customer_session)
    session.flush()
    return customer_session


def get_active_customer_by_session_token_hash(
    session: Session,
    session_token_hash: str,
    now: datetime,
) -> Customer | None:
    statement = (
        select(Customer)
        .join(CustomerSession, CustomerSession.customer_id == Customer.id)
        .where(CustomerSession.session_token_hash == session_token_hash)
        .where(CustomerSession.revoked_at.is_(None))
        .where(CustomerSession.expires_at > now)
        .where(Customer.status == "active")
        .order_by(CustomerSession.id.desc())
    )
    return session.scalar(statement)



def get_active_customer_session_by_token_hash(
    session: Session,
    session_token_hash: str,
    now: datetime,
) -> CustomerSession | None:
    statement = (
        select(CustomerSession)
        .join(Customer, Customer.id == CustomerSession.customer_id)
        .where(CustomerSession.session_token_hash == session_token_hash)
        .where(CustomerSession.revoked_at.is_(None))
        .where(CustomerSession.expires_at > now)
        .where(Customer.status == "active")
        .order_by(CustomerSession.id.desc())
    )
    return session.scalar(statement)



def revoke_customer_session(
    session: Session,
    customer_session: CustomerSession,
    revoked_at: datetime,
) -> CustomerSession:
    customer_session.revoked_at = revoked_at
    session.flush()
    return customer_session
