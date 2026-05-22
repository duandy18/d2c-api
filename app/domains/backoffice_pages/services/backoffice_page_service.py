from sqlalchemy.orm import Session

from app.domains.backoffice_pages.contracts.backoffice_page_contract import (
    BackofficePageContract,
    BackofficePageHealthResponse,
    BackofficePageNavigationResponse,
    BackofficePageNode,
    BackofficePageRegistryResponse,
)
from app.domains.backoffice_pages.models.backoffice_page import BackofficePage
from app.domains.backoffice_pages.repos.backoffice_page_repo import (
    list_backoffice_pages,
)


def get_backoffice_page_health() -> BackofficePageHealthResponse:
    return BackofficePageHealthResponse(
        status="ok",
        module="backoffice_pages",
        surface="merchant_navigation",
    )


def get_backoffice_page_registry(session: Session) -> BackofficePageRegistryResponse:
    pages = list_backoffice_pages(session)
    return BackofficePageRegistryResponse(
        count=len(pages),
        pages=[_build_page_contract(page) for page in pages],
    )


def get_backoffice_page_navigation(session: Session) -> BackofficePageNavigationResponse:
    pages = [
        page
        for page in list_backoffice_pages(session)
        if page.is_enabled and page.is_visible and page.implementation_status != "hidden"
    ]

    nodes = {page.page_code: _build_page_node(page) for page in pages}

    roots: list[BackofficePageNode] = []

    for page in pages:
        node = nodes[page.page_code]

        if page.parent_code is None or page.parent_code not in nodes:
            roots.append(node)
            continue

        nodes[page.parent_code].children.append(node)

    _sort_nodes(roots)

    return BackofficePageNavigationResponse(
        surface="backoffice",
        version=1,
        pages=roots,
    )


def _build_page_contract(page: BackofficePage) -> BackofficePageContract:
    return BackofficePageContract(
        id=page.id,
        page_code=page.page_code,
        parent_code=page.parent_code,
        level=page.level,
        title=page.title,
        route_path=page.route_path,
        component_key=page.component_key,
        icon=page.icon,
        sort_order=page.sort_order,
        is_enabled=page.is_enabled,
        is_visible=page.is_visible,
        implementation_status=page.implementation_status,
        data_status=page.data_status,
        required_permission=page.required_permission,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


def _build_page_node(page: BackofficePage) -> BackofficePageNode:
    return BackofficePageNode(
        page_code=page.page_code,
        parent_code=page.parent_code,
        level=page.level,
        title=page.title,
        route_path=page.route_path,
        component_key=page.component_key,
        icon=page.icon,
        sort_order=page.sort_order,
        implementation_status=page.implementation_status,
        data_status=page.data_status,
        required_permission=page.required_permission,
        children=[],
    )


def _sort_nodes(nodes: list[BackofficePageNode]) -> None:
    nodes.sort(key=lambda node: (node.sort_order, node.page_code))

    for node in nodes:
        _sort_nodes(node.children)
