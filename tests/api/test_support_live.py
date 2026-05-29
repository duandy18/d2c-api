from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


def unique_email(prefix: str = "support-live") -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def force_all_agents_offline() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE d2c_support_agent_presence
                    SET presence_status = 'offline',
                        active_session_count = 0,
                        last_heartbeat_at = NULL,
                        updated_at = now()
                    """
                )
            )
    finally:
        engine.dispose()


def create_agent(client: TestClient, *, display_name: str = "Live Agent") -> str:
    response = client.post(
        "/backoffice/support/agents",
        headers=BACKOFFICE_HEADERS,
        json={
            "display_name": display_name,
            "email": unique_email("agent"),
        },
    )
    assert response.status_code == 201
    return str(response.json()["agent_code"])


def agent_headers(agent_code: str) -> dict[str, str]:
    return {
        **BACKOFFICE_HEADERS,
        "X-Support-Agent-Code": agent_code,
    }


def mark_agent_online(client: TestClient, agent_code: str) -> None:
    response = client.post(
        f"/backoffice/support/agents/{agent_code}/presence",
        headers=BACKOFFICE_HEADERS,
        json={
            "presence_status": "online",
            "max_active_sessions": 3,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_code"] == agent_code
    assert payload["presence_status"] == "online"


def create_live_session(client: TestClient) -> tuple[str, str]:
    response = client.post(
        "/support/live/sessions",
        json={
            "anonymous_id": unique_code("anon"),
            "session_code": unique_code("sess"),
            "contact_name": "Live Customer",
            "contact_email": unique_email("customer"),
            "opening_message": "在线吗？我想咨询猫粮。",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["session_code"].startswith("LIVE-")
    assert payload["session_token"]
    assert payload["status"] == "waiting"
    assert payload["conversation_code"].startswith("SUP-")
    assert [message["sender_type"] for message in payload["messages"]] == ["customer", "system"]
    return str(payload["session_code"]), str(payload["session_token"])


def test_support_live_availability_offline_by_default() -> None:
    force_all_agents_offline()
    client = TestClient(app)

    response = client.get("/support/live/availability")

    assert response.status_code == 200
    payload = response.json()
    assert payload["availability_status"] == "offline"
    assert payload["available_agent_count"] == 0


def test_support_live_agent_presence_controls_availability() -> None:
    force_all_agents_offline()
    client = TestClient(app)
    agent_code = create_agent(client)

    mark_agent_online(client, agent_code)

    response = client.get("/support/live/availability")

    assert response.status_code == 200
    payload = response.json()
    assert payload["availability_status"] == "online"
    assert payload["available_agent_count"] >= 1


def test_support_live_session_requires_available_agent() -> None:
    force_all_agents_offline()
    client = TestClient(app)

    response = client.post(
        "/support/live/sessions",
        json={
            "anonymous_id": unique_code("anon"),
            "session_code": unique_code("sess"),
            "opening_message": "有没有客服？",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "support_live_unavailable"}


def test_support_live_chat_flow_with_polling() -> None:
    force_all_agents_offline()
    client = TestClient(app)
    agent_code = create_agent(client)
    mark_agent_online(client, agent_code)

    session_code, session_token = create_live_session(client)

    list_response = client.get(
        "/backoffice/support/live/sessions",
        headers=BACKOFFICE_HEADERS,
        params={"status": "waiting"},
    )
    assert list_response.status_code == 200
    assert session_code in [row["session_code"] for row in list_response.json()["sessions"]]

    accept_response = client.post(
        f"/backoffice/support/live/sessions/{session_code}/accept",
        headers=agent_headers(agent_code),
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "active"
    assert accept_response.json()["assigned_agent_code"] == agent_code

    agent_reply_response = client.post(
        f"/backoffice/support/live/sessions/{session_code}/messages",
        headers=agent_headers(agent_code),
        json={"body": "您好，我是在线客服。"},
    )
    assert agent_reply_response.status_code == 200
    assert agent_reply_response.json()["messages"][-1]["sender_type"] == "agent"

    customer_poll_response = client.get(
        f"/support/live/sessions/{session_code}",
        params={"session_token": session_token},
    )
    assert customer_poll_response.status_code == 200
    assert customer_poll_response.json()["messages"][-1]["body"] == "您好，我是在线客服。"

    customer_message_response = client.post(
        f"/support/live/sessions/{session_code}/messages",
        json={
            "session_token": session_token,
            "body": "我想了解发货时间。",
        },
    )
    assert customer_message_response.status_code == 200
    assert customer_message_response.json()["messages"][-1]["sender_type"] == "customer"

    end_response = client.post(
        f"/backoffice/support/live/sessions/{session_code}/end",
        headers=agent_headers(agent_code),
        json={"reason": "咨询结束"},
    )
    assert end_response.status_code == 200
    assert end_response.json()["status"] == "ended"

    closed_response = client.post(
        f"/support/live/sessions/{session_code}/messages",
        json={
            "session_token": session_token,
            "body": "结束后不能继续发。",
        },
    )
    assert closed_response.status_code == 409
    assert closed_response.json() == {"detail": "support_live_session_closed"}


def test_support_live_anonymous_session_requires_valid_token() -> None:
    force_all_agents_offline()
    client = TestClient(app)
    agent_code = create_agent(client)
    mark_agent_online(client, agent_code)
    session_code, session_token = create_live_session(client)

    missing_response = client.get(f"/support/live/sessions/{session_code}")
    wrong_response = client.get(
        f"/support/live/sessions/{session_code}",
        params={"session_token": "wrong-token-value-with-enough-length"},
    )
    correct_response = client.get(
        f"/support/live/sessions/{session_code}",
        params={"session_token": session_token},
    )

    assert missing_response.status_code == 401
    assert missing_response.json() == {"detail": "support_live_session_token_required"}

    assert wrong_response.status_code == 401
    assert wrong_response.json() == {"detail": "support_live_session_token_invalid"}

    assert correct_response.status_code == 200
    assert correct_response.json()["session_code"] == session_code


def test_support_live_routes_and_openapi_are_registered() -> None:
    route_paths = {route.path for route in app.routes}
    for path in (
        "/support/live/availability",
        "/support/live/sessions",
        "/support/live/sessions/{session_code}",
        "/support/live/sessions/{session_code}/messages",
        "/support/live/sessions/{session_code}/end",
        "/backoffice/support/agents/presence",
        "/backoffice/support/agents/{agent_code}/presence",
        "/backoffice/support/live/sessions",
        "/backoffice/support/live/sessions/{session_code}",
        "/backoffice/support/live/sessions/{session_code}/accept",
        "/backoffice/support/live/sessions/{session_code}/messages",
        "/backoffice/support/live/sessions/{session_code}/end",
    ):
        assert path in route_paths
        assert path in app.openapi()["paths"]
