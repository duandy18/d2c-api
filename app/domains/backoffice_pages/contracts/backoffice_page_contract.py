from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ImplementationStatus = Literal["ready", "planned", "hidden"]
DataStatus = Literal["connected", "placeholder", "disabled"]


class BackofficePageContract(BaseModel):
    id: int
    page_code: str
    parent_code: str | None
    level: int
    title: str
    route_path: str
    component_key: str
    icon: str | None
    sort_order: int
    is_enabled: bool
    is_visible: bool
    implementation_status: ImplementationStatus
    data_status: DataStatus
    required_permission: str | None
    created_at: datetime
    updated_at: datetime


class BackofficePageNode(BaseModel):
    page_code: str
    parent_code: str | None
    level: int
    title: str
    route_path: str
    component_key: str
    icon: str | None
    sort_order: int
    implementation_status: ImplementationStatus
    data_status: DataStatus
    required_permission: str | None
    children: list["BackofficePageNode"]


class BackofficePageHealthResponse(BaseModel):
    status: str
    module: str
    surface: str


class BackofficePageRegistryResponse(BaseModel):
    count: int
    pages: list[BackofficePageContract]


class BackofficePageNavigationResponse(BaseModel):
    surface: str
    version: int
    pages: list[BackofficePageNode]
