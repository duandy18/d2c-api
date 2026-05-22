import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.parametrize(
    "origin",
    [
        "http://127.0.0.1:5177",
        "http://localhost:5177",
        "http://127.0.0.1:5178",
        "http://localhost:5178",
    ],
)
def test_local_web_origins_can_preflight_health(origin: str) -> None:
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "http://127.0.0.1:5178",
        "http://localhost:5178",
    ],
)
def test_backoffice_origin_can_preflight_navigation_with_client_header(origin: str) -> None:
    client = TestClient(app)

    response = client.options(
        "/backoffice/pages/navigation",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-backoffice-client",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "x-backoffice-client" in response.headers[
        "access-control-allow-headers"
    ].lower()
