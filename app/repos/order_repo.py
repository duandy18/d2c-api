from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartLine
from app.models.catalog import Product, ProductSku
from app.models.order import D2COrder, D2COrderLine, D2CPayment


def get_cart_by_code(
    session: Session,
    cart_code: str,
) -> Cart | None:
    statement = select(Cart).where(Cart.cart_code == cart_code)
    return session.scalar(statement)


def _cart_lines_query(cart_id: int) -> Select[tuple[CartLine, Product, ProductSku]]:
    return (
        select(CartLine, Product, ProductSku)
        .join(Product, Product.id == CartLine.product_id)
        .join(ProductSku, ProductSku.id == CartLine.sku_id)
        .where(CartLine.cart_id == cart_id)
        .order_by(CartLine.id)
    )


def list_cart_line_rows_for_checkout(
    session: Session,
    cart_id: int,
) -> list[tuple[CartLine, Product, ProductSku]]:
    return list(session.execute(_cart_lines_query(cart_id)).all())


def create_order(
    session: Session,
    order: D2COrder,
) -> D2COrder:
    session.add(order)
    session.flush()
    return order


def create_order_line(
    session: Session,
    order_line: D2COrderLine,
) -> D2COrderLine:
    session.add(order_line)
    session.flush()
    return order_line


def create_payment(
    session: Session,
    payment: D2CPayment,
) -> D2CPayment:
    session.add(payment)
    session.flush()
    return payment


def get_order_by_no_for_customer(
    session: Session,
    order_no: str,
    customer_id: int,
) -> D2COrder | None:
    statement = (
        select(D2COrder)
        .where(D2COrder.order_no == order_no)
        .where(D2COrder.customer_id == customer_id)
    )
    return session.scalar(statement)


def list_order_lines(
    session: Session,
    order_id: int,
) -> list[D2COrderLine]:
    statement = (
        select(D2COrderLine).where(D2COrderLine.order_id == order_id).order_by(D2COrderLine.id)
    )
    return list(session.scalars(statement).all())


def get_latest_payment_by_order_id(
    session: Session,
    order_id: int,
) -> D2CPayment | None:
    statement = (
        select(D2CPayment).where(D2CPayment.order_id == order_id).order_by(D2CPayment.id.desc())
    )
    return session.scalar(statement)
