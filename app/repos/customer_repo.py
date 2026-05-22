from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import (
    Customer,
    CustomerPasswordCredential,
    CustomerSession,
)


def get_customer_by_email(session: Session, email: str) -> Customer | None:
    statement = select(Customer).where(Customer.email == email)
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
