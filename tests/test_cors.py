from fastapi.testclient import TestClient

from app.main import app


def test_local_web_origin_can_preflight_health() -> None:
    client = TestClient(app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5177",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5177"
