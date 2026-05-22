from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.backoffice_pages.contracts.backoffice_page_contract import (
    BackofficePageHealthResponse,
    BackofficePageNavigationResponse,
    BackofficePageRegistryResponse,
)
from app.domains.backoffice_pages.services.backoffice_page_service import (
    get_backoffice_page_health,
    get_backoffice_page_navigation,
    get_backoffice_page_registry,
)

router = APIRouter(prefix="/backoffice/pages", tags=["backoffice-pages"])

SessionDep = Annotated[Session, Depends(get_session)]


def require_backoffice_client(
    x_backoffice_client: Annotated[str | None, Header(alias="X-Backoffice-Client")] = None,
) -> str:
    if x_backoffice_client != "d2c-backoffice":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="backoffice_client_required",
        )

    return x_backoffice_client


BackofficeClientDep = Annotated[str, Depends(require_backoffice_client)]


@router.get("/health", response_model=BackofficePageHealthResponse)
def backoffice_pages_health(
    _: BackofficeClientDep,
) -> BackofficePageHealthResponse:
    return get_backoffice_page_health()


@router.get("/registry", response_model=BackofficePageRegistryResponse)
def backoffice_pages_registry(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePageRegistryResponse:
    return get_backoffice_page_registry(session)


@router.get("/navigation", response_model=BackofficePageNavigationResponse)
def backoffice_pages_navigation(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePageNavigationResponse:
    return get_backoffice_page_navigation(session)
