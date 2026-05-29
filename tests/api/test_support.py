from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app


def unique_email() -> str:
    return f"support-customer-{uuid4().hex}@example.com"


def unique_phone() -> str:
    return f"188{uuid4().hex[:8]}"


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def register_customer(client: TestClient, *, display_name: str = "Support Customer") -> str:
    response = client.post(
        "/customers/register",
        json={
            "email": unique_email(),
            "password": "StrongPass123",
            "display_name": display_name,
            "phone": unique_phone(),
        },
    )
    assert response.status_code == 201
    return str(response.json()["access_token"])


def create_anonymous_conversation(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/support/conversations",
        json={
            "anonymous_id": f"anon-{uuid4().hex}",
            "session_code": f"sess-{uuid4().hex}",
            "contact_name": "Anonymous Support User",
            "contact_email": unique_email(),
            "topic": "product_question",
            "related_order_no": None,
            "message": "这个商品适合幼猫吗？",
        },
    )
    assert response.status_code == 201
    return response.json()


def get_support_row(conversation_code: str) -> dict[str, object]:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT
                          id,
                          conversation_code,
                          customer_id,
                          contact_email,
                          contact_phone,
                          topic,
                          related_order_no,
                          status,
                          source,
                          conversation_token_hash
                        FROM d2c_support_conversations
                        WHERE conversation_code = :conversation_code
                        """
                    ),
                    {"conversation_code": conversation_code},
                )
                .mappings()
                .one()
            )
            return dict(row)
    finally:
        engine.dispose()


def list_support_message_senders(conversation_code: str) -> list[str]:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                        SELECT m.sender_type
                        FROM d2c_support_messages m
                        JOIN d2c_support_conversations c ON c.id = m.conversation_id
                        WHERE c.conversation_code = :conversation_code
                        ORDER BY m.created_at, m.id
                        """
                    ),
                    {"conversation_code": conversation_code},
                )
                .scalars()
                .all()
            )
            return [str(row) for row in rows]
    finally:
        engine.dispose()


def test_support_health() -> None:
    client = TestClient(app)

    response = client.get("/support/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "support",
        "conversation_storage": "d2c_support_conversations",
        "message_storage": "d2c_support_messages",
    }


def test_support_page_surface_exists() -> None:
    client = TestClient(app)

    response = client.get("/storefront/pages")

    assert response.status_code == 200

    pages = {page["page_code"]: page for page in response.json()["pages"]}
    assert pages["customer_service"]["page_type"] == "customer_service"
    assert pages["customer_service"]["route_path"] == "/support"
    assert pages["customer_service"]["title"] == "客户服务"
    assert pages["customer_service"]["auth_required"] is False
    assert pages["customer_service"]["navigation_label"] == "客户服务"
    assert pages["customer_service"]["navigation_group"] == "support"
    assert pages["customer_service"]["sort_order"] == 80


def test_anonymous_support_conversation_requires_email_or_phone() -> None:
    client = TestClient(app)

    response = client.post(
        "/support/conversations",
        json={
            "anonymous_id": f"anon-{uuid4().hex}",
            "session_code": f"sess-{uuid4().hex}",
            "topic": "product_question",
            "message": "我想咨询商品。",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "support_contact_email_or_phone_required"}


def test_anonymous_support_conversation_creates_customer_and_system_messages() -> None:
    client = TestClient(app)

    payload = create_anonymous_conversation(client)

    assert payload["conversation_code"].startswith("SUP-")
    assert payload["conversation_token"]
    assert payload["topic"] == "product_question"
    assert payload["status"] == "open"
    assert payload["source"] == "storefront"
    assert [message["sender_type"] for message in payload["messages"]] == ["customer", "system"]
    assert payload["messages"][0]["body"] == "这个商品适合幼猫吗？"
    assert payload["messages"][1]["body"] == "我们已收到您的消息，客服会尽快回复。"

    row = get_support_row(str(payload["conversation_code"]))
    assert row["customer_id"] is None
    assert row["conversation_token_hash"]
    assert row["conversation_token_hash"] != payload["conversation_token"]
    assert list_support_message_senders(str(payload["conversation_code"])) == ["customer", "system"]


def test_logged_in_support_conversation_binds_customer_id() -> None:
    client = TestClient(app)
    token = register_customer(client, display_name="Logged Support Customer")

    response = client.post(
        "/support/conversations",
        json={
            "topic": "order_status",
            "related_order_no": "ORD-TEST-SUPPORT",
            "message": "请帮我看一下订单状态。",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["conversation_token"] is None
    assert payload["contact_name"] == "Logged Support Customer"
    assert payload["topic"] == "order_status"
    assert payload["related_order_no"] == "ORD-TEST-SUPPORT"

    row = get_support_row(str(payload["conversation_code"]))
    assert row["customer_id"] is not None
    assert row["conversation_token_hash"] is None


def test_customer_can_continue_support_conversation() -> None:
    client = TestClient(app)
    token = register_customer(client)

    create_response = client.post(
        "/support/conversations",
        json={
            "topic": "shipping",
            "message": "什么时候发货？",
        },
        headers=auth_headers(token),
    )
    assert create_response.status_code == 201

    conversation_code = create_response.json()["conversation_code"]
    message_response = client.post(
        f"/support/conversations/{conversation_code}/messages",
        json={
            "body": "我补充一下，地址是洛杉矶。",
        },
        headers=auth_headers(token),
    )

    assert message_response.status_code == 200

    payload = message_response.json()
    assert payload["conversation_code"] == conversation_code
    assert payload["messages"][-1]["sender_type"] == "customer"
    assert payload["messages"][-1]["body"] == "我补充一下，地址是洛杉矶。"


def test_other_customer_cannot_read_support_conversation() -> None:
    client = TestClient(app)
    first_token = register_customer(client, display_name="First Support Customer")
    second_token = register_customer(client, display_name="Second Support Customer")

    create_response = client.post(
        "/support/conversations",
        json={
            "topic": "payment_issue",
            "message": "支付成功后页面没跳转。",
        },
        headers=auth_headers(first_token),
    )
    assert create_response.status_code == 201

    conversation_code = create_response.json()["conversation_code"]
    response = client.get(
        f"/support/conversations/{conversation_code}",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "support_conversation_not_found"}


def test_anonymous_support_conversation_requires_valid_token_to_read() -> None:
    client = TestClient(app)

    payload = create_anonymous_conversation(client)
    conversation_code = payload["conversation_code"]
    conversation_token = payload["conversation_token"]

    missing_response = client.get(f"/support/conversations/{conversation_code}")
    wrong_response = client.get(
        f"/support/conversations/{conversation_code}",
        params={"conversation_token": "wrong-token-value-with-enough-length"},
    )
    correct_response = client.get(
        f"/support/conversations/{conversation_code}",
        params={"conversation_token": conversation_token},
    )

    assert missing_response.status_code == 401
    assert missing_response.json() == {"detail": "support_conversation_token_required"}

    assert wrong_response.status_code == 401
    assert wrong_response.json() == {"detail": "support_conversation_token_invalid"}

    assert correct_response.status_code == 200
    assert correct_response.json()["conversation_code"] == conversation_code


def test_anonymous_support_conversation_can_continue_with_token() -> None:
    client = TestClient(app)

    payload = create_anonymous_conversation(client)
    conversation_code = str(payload["conversation_code"])
    conversation_token = str(payload["conversation_token"])

    response = client.post(
        f"/support/conversations/{conversation_code}/messages",
        json={
            "conversation_token": conversation_token,
            "body": "我再补充一个问题。",
        },
    )

    assert response.status_code == 200
    assert response.json()["messages"][-1]["body"] == "我再补充一个问题。"


def test_logged_in_customer_can_list_own_support_conversations() -> None:
    client = TestClient(app)
    first_token = register_customer(client)
    second_token = register_customer(client)

    first_response = client.post(
        "/support/conversations",
        json={
            "topic": "returns_after_sales",
            "message": "我要咨询退换货。",
        },
        headers=auth_headers(first_token),
    )
    second_response = client.post(
        "/support/conversations",
        json={
            "topic": "payment_issue",
            "message": "我要咨询支付。",
        },
        headers=auth_headers(second_token),
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    list_response = client.get("/support/conversations", headers=auth_headers(first_token))

    assert list_response.status_code == 200

    payload = list_response.json()
    codes = [conversation["conversation_code"] for conversation in payload["conversations"]]
    assert first_response.json()["conversation_code"] in codes
    assert second_response.json()["conversation_code"] not in codes


def test_support_routes_and_openapi_are_registered() -> None:
    route_paths = {route.path for route in app.routes}
    assert "/support/health" in route_paths
    assert "/support/conversations" in route_paths
    assert "/support/conversations/{conversation_code}" in route_paths
    assert "/support/conversations/{conversation_code}/messages" in route_paths

    openapi_paths = app.openapi()["paths"]
    assert "/support/health" in openapi_paths
    assert "/support/conversations" in openapi_paths
    assert "/support/conversations/{conversation_code}" in openapi_paths
    assert "/support/conversations/{conversation_code}/messages" in openapi_paths
