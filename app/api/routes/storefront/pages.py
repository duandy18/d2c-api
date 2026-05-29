"""Storefront page route surface."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.site_config.contracts.storefront_page_contract import StorefrontPagesResponse
from app.domains.site_config.services.storefront_page_service import get_storefront_pages

router = APIRouter(prefix="/storefront", tags=["storefront"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/pages", response_model=StorefrontPagesResponse)
def storefront_pages(session: SessionDep) -> StorefrontPagesResponse:
    return get_storefront_pages(session)
