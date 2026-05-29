from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


def unique_email(prefix: str = "support") -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def agent_headers(agent_code: str) -> dict[str, str]:
    return {
        **BACKOFFICE_HEADERS,
        "X-Support-Agent-Code": agent_code,
    }


def create_agent(client: TestClient, *, display_name: str = "Support Agent") -> str:
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


def create_customer_conversation(client: TestClient) -> tuple[str, str]:
    response = client.post(
        "/support/conversations",
        json={
            "anonymous_id": f"anon-{uuid4().hex}",
            "session_code": f"sess-{uuid4().hex}",
            "contact_name": "Workbench Customer",
            "contact_email": unique_email("customer"),
            "topic": "product_question",
            "message": "请问这款猫粮适合幼猫吗？",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "pending_agent"
    assert payload["conversation_token"]
    return str(payload["conversation_code"]), str(payload["conversation_token"])


def test_backoffice_support_requires_backoffice_client() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/support/health")

    assert response.status_code == 401
    assert response.json() == {"detail": "backoffice_client_required"}


def test_backoffice_support_health_and_agent_profile() -> None:
    client = TestClient(app)

    health_response = client.get("/backoffice/support/health", headers=BACKOFFICE_HEADERS)
    assert health_response.status_code == 200
    assert health_response.json()["workbench"] == "d2c_support_workbench"

    agent_code = create_agent(client, display_name="Agent One")

    list_response = client.get("/backoffice/support/agents", headers=BACKOFFICE_HEADERS)
    assert list_response.status_code == 200
    assert agent_code in [agent["agent_code"] for agent in list_response.json()["agents"]]


def test_backoffice_support_can_list_and_read_conversation() -> None:
    client = TestClient(app)
    conversation_code, _conversation_token = create_customer_conversation(client)

    list_response = client.get(
        "/backoffice/support/conversations",
        headers=BACKOFFICE_HEADERS,
        params={"status": "pending_agent"},
    )
    assert list_response.status_code == 200
    codes = [row["conversation_code"] for row in list_response.json()["conversations"]]
    assert conversation_code in codes

    detail_response = client.get(
        f"/backoffice/support/conversations/{conversation_code}",
        headers=BACKOFFICE_HEADERS,
    )
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["conversation_code"] == conversation_code
    assert payload["contact"]["contact_email"]
    assert [message["sender_type"] for message in payload["messages"]] == ["customer", "system"]


def test_backoffice_support_assign_reply_customer_reply_and_close_flow() -> None:
    client = TestClient(app)
    conversation_code, conversation_token = create_customer_conversation(client)
    agent_code = create_agent(client, display_name="Flow Agent")

    assign_response = client.post(
        f"/backoffice/support/conversations/{conversation_code}/assign",
        headers=agent_headers(agent_code),
        json={"agent_code": agent_code},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["assigned_agent"]["agent_code"] == agent_code

    reply_response = client.post(
        f"/backoffice/support/conversations/{conversation_code}/messages",
        headers=agent_headers(agent_code),
        json={"body": "可以，建议按包装上的年龄段喂食。", "visibility": "public"},
    )
    assert reply_response.status_code == 200
    assert reply_response.json()["status"] == "pending_customer"
    assert reply_response.json()["messages"][-1]["sender_type"] == "agent"
    assert reply_response.json()["messages"][-1]["agent_code"] == agent_code

    customer_response = client.post(
        f"/support/conversations/{conversation_code}/messages",
        json={
            "conversation_token": conversation_token,
            "body": "谢谢，我再确认一下规格。",
        },
    )
    assert customer_response.status_code == 200
    assert customer_response.json()["status"] == "pending_agent"

    close_response = client.post(
        f"/backoffice/support/conversations/{conversation_code}/close",
        headers=agent_headers(agent_code),
        json={"reason": "问题已解决"},
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"
    assert close_response.json()["closed_at"] is not None

    closed_agent_reply_response = client.post(
        f"/backoffice/support/conversations/{conversation_code}/messages",
        headers=agent_headers(agent_code),
        json={"body": "关闭后不能继续回复。", "visibility": "public"},
    )
    assert closed_agent_reply_response.status_code == 409
    assert closed_agent_reply_response.json() == {"detail": "support_conversation_closed"}

    closed_customer_reply_response = client.post(
        f"/support/conversations/{conversation_code}/messages",
        json={
            "conversation_token": conversation_token,
            "body": "关闭后我不能继续追问。",
        },
    )
    assert closed_customer_reply_response.status_code == 409
    assert closed_customer_reply_response.json() == {"detail": "support_conversation_closed"}

    events_response = client.get(
        f"/backoffice/support/conversations/{conversation_code}/events",
        headers=BACKOFFICE_HEADERS,
    )
    assert events_response.status_code == 200
    event_types = [event["event_type"] for event in events_response.json()["events"]]
    assert "conversation_created" in event_types
    assert "customer_message" in event_types
    assert "system_message" in event_types
    assert "assigned" in event_types
    assert "agent_message" in event_types
    assert "closed" in event_types


def test_backoffice_support_requires_active_agent_for_write_actions() -> None:
    client = TestClient(app)
    conversation_code, _conversation_token = create_customer_conversation(client)

    response = client.post(
        f"/backoffice/support/conversations/{conversation_code}/messages",
        headers=BACKOFFICE_HEADERS,
        json={"body": "没有客服身份不能回复。", "visibility": "public"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "support_agent_required"}


def test_backoffice_support_routes_and_openapi_are_registered() -> None:
    route_paths = {route.path for route in app.routes}
    for path in (
        "/backoffice/support/health",
        "/backoffice/support/agents",
        "/backoffice/support/conversations",
        "/backoffice/support/conversations/{conversation_code}",
        "/backoffice/support/conversations/{conversation_code}/assign",
        "/backoffice/support/conversations/{conversation_code}/messages",
        "/backoffice/support/conversations/{conversation_code}/close",
        "/backoffice/support/conversations/{conversation_code}/events",
    ):
        assert path in route_paths
        assert path in app.openapi()["paths"]
