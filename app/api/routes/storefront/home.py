"""Storefront home routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.site_config.contracts.storefront_home_contract import StorefrontHomeResponse
from app.domains.site_config.services.storefront_home_service import get_storefront_home

router = APIRouter(prefix="/storefront", tags=["storefront"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/home", response_model=StorefrontHomeResponse)
def storefront_home(session: SessionDep) -> StorefrontHomeResponse:
    return get_storefront_home(session)
