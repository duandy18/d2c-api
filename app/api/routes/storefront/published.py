"""Runtime published model inspection routes.

These routes expose service-client-gated runtime inspection surfaces.
Legacy published products/skus/prices/promotions debug routes are retired.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.published.contracts.published_contract import (
    PublishedCouponsResponse,
    PublishedHealthResponse,
    PublishSyncRunsResponse,
)
from app.domains.published.services.published_service import (
    get_publish_sync_runs,
    get_published_coupons,
    get_published_health,
)

router = APIRouter(prefix="/published", tags=["published"])
SessionDep = Annotated[Session, Depends(get_session)]


def require_service_client(
    x_service_client: Annotated[str | None, Header(alias="X-Service-Client")] = None,
) -> None:
    if x_service_client != "d2c-service":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="service_client_required",
        )


ServiceClientDep = Annotated[None, Depends(require_service_client)]


@router.get("/health", response_model=PublishedHealthResponse)
def published_health(_: ServiceClientDep) -> PublishedHealthResponse:
    return get_published_health()


@router.get("/coupons", response_model=PublishedCouponsResponse)
def published_coupons(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishedCouponsResponse:
    return get_published_coupons(session)


@router.get("/sync-runs", response_model=PublishSyncRunsResponse)
def published_sync_runs(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishSyncRunsResponse:
    return get_publish_sync_runs(session)
