"""Storefront page surface service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domains.site_config.contracts.storefront_page_contract import (
    StorefrontPageRoute,
    StorefrontPagesResponse,
)
from app.domains.site_config.models import StorefrontPage
from app.domains.site_config.repos.storefront_site_config_repo import (
    get_site,
    list_pages,
)


def _page_route_schema(page: StorefrontPage) -> StorefrontPageRoute:
    return StorefrontPageRoute(
        page_code=page.page_code,
        page_type=page.page_type,
        route_path=page.route_path,
        title=page.title,
        description=page.description,
        status=page.status,
        auth_required=page.auth_required,
        navigation_label=page.navigation_label,
        navigation_group=page.navigation_group,
        sort_order=page.sort_order,
    )


def get_storefront_pages(session: Session) -> StorefrontPagesResponse:
    site = get_site(session)
    if site is None or site.status != "active":
        return StorefrontPagesResponse(count=0)

    pages = [
        _page_route_schema(page)
        for page in list_pages(session, site.id, active_only=True)
    ]

    return StorefrontPagesResponse(pages=pages, count=len(pages))
