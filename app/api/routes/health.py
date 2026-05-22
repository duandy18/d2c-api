from fastapi import APIRouter, Request

from app.core.config import D2CSettings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    settings: D2CSettings = request.app.state.settings

    return {
        "status": "ok",
        "environment": settings.environment,
        "app_code": settings.app_code,
        "service": settings.service_name,
        "api_path": settings.api_path,
    }
