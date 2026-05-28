"""Storefront site configuration repositories."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.site_config.models import (
    StorefrontPage,
    StorefrontPageSlot,
    StorefrontSite,
    StorefrontSlotItem,
    StorefrontSlotOfferPosition,
    StorefrontThemeSetting,
)


def get_site(session: Session, site_code: str = "default") -> StorefrontSite | None:
    return session.scalar(select(StorefrontSite).where(StorefrontSite.site_code == site_code))


def get_active_theme(
    session: Session,
    site_id: int,
) -> StorefrontThemeSetting | None:
    statement = (
        select(StorefrontThemeSetting)
        .where(StorefrontThemeSetting.site_id == site_id)
        .where(StorefrontThemeSetting.is_active.is_(True))
        .order_by(StorefrontThemeSetting.id.desc())
        .limit(1)
    )
    return session.scalar(statement)


def get_page(
    session: Session,
    site_id: int,
    page_code: str = "home",
) -> StorefrontPage | None:
    statement = (
        select(StorefrontPage)
        .where(StorefrontPage.site_id == site_id)
        .where(StorefrontPage.page_code == page_code)
        .limit(1)
    )
    return session.scalar(statement)


def list_slots(
    session: Session,
    page_id: int,
) -> list[StorefrontPageSlot]:
    statement = (
        select(StorefrontPageSlot)
        .where(StorefrontPageSlot.page_id == page_id)
        .order_by(StorefrontPageSlot.sort_order, StorefrontPageSlot.id)
    )
    return list(session.scalars(statement).all())


def get_slot(
    session: Session,
    page_id: int,
    slot_code: str,
) -> StorefrontPageSlot | None:
    statement = (
        select(StorefrontPageSlot)
        .where(StorefrontPageSlot.page_id == page_id)
        .where(StorefrontPageSlot.slot_code == slot_code)
        .limit(1)
    )
    return session.scalar(statement)


def list_items_by_slot_ids(
    session: Session,
    slot_ids: list[int],
) -> dict[int, list[StorefrontSlotItem]]:
    if not slot_ids:
        return {}

    statement = (
        select(StorefrontSlotItem)
        .where(StorefrontSlotItem.slot_id.in_(slot_ids))
        .order_by(StorefrontSlotItem.slot_id, StorefrontSlotItem.sort_order, StorefrontSlotItem.id)
    )
    result: dict[int, list[StorefrontSlotItem]] = {}
    for item in session.scalars(statement).all():
        result.setdefault(item.slot_id, []).append(item)
    return result


def list_offer_positions_by_slot_ids(
    session: Session,
    slot_ids: list[int],
) -> dict[int, list[StorefrontSlotOfferPosition]]:
    if not slot_ids:
        return {}

    statement = (
        select(StorefrontSlotOfferPosition)
        .where(StorefrontSlotOfferPosition.slot_id.in_(slot_ids))
        .order_by(
            StorefrontSlotOfferPosition.slot_id,
            StorefrontSlotOfferPosition.sort_order,
            StorefrontSlotOfferPosition.id,
        )
    )
    result: dict[int, list[StorefrontSlotOfferPosition]] = {}
    for position in session.scalars(statement).all():
        result.setdefault(position.slot_id, []).append(position)
    return result


def delete_slot_items(session: Session, slot_id: int) -> None:
    session.execute(delete(StorefrontSlotItem).where(StorefrontSlotItem.slot_id == slot_id))


def delete_slot_offer_positions(session: Session, slot_id: int) -> None:
    session.execute(
        delete(StorefrontSlotOfferPosition).where(StorefrontSlotOfferPosition.slot_id == slot_id)
    )
