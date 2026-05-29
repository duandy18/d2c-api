from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def unique_email() -> str:
    return f"customer-{uuid4().hex}@example.com"


def unique_phone() -> str:
    return f"188{uuid4().hex[:8]}"


def test_customers_health() -> None:
    client = TestClient(app)

    response = client.get("/customers/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "customers",
        "auth_mode": "password",
    }


def test_customer_register_and_login_with_password() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Test Customer",
            "phone": None,
        },
    )

    assert register_response.status_code == 201

    register_payload = register_response.json()
    assert register_payload["token_type"] == "Bearer"
    assert register_payload["access_token"]
    assert register_payload["customer"]["email"] == email
    assert register_payload["customer"]["display_name"] == "Test Customer"

    login_response = client.post(
        "/customers/login",
        json={
            "email": email,
            "password": "StrongPass123",
        },
    )

    assert login_response.status_code == 200

    login_payload = login_response.json()
    assert login_payload["token_type"] == "Bearer"
    assert login_payload["access_token"]
    assert login_payload["customer"]["email"] == email
    assert login_payload["customer"]["last_login_at"] is not None


def test_customer_register_rejects_duplicate_email() -> None:
    client = TestClient(app)
    email = unique_email()
    payload = {
        "email": email,
        "password": "StrongPass123",
        "display_name": "Test Customer",
        "phone": None,
    }

    first_response = client.post("/customers/register", json=payload)
    second_response = client.post("/customers/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "customer_email_already_registered"}


def test_customer_register_rejects_duplicate_phone() -> None:
    client = TestClient(app)
    phone = f"phone-{uuid4().hex[:20]}"
    first_payload = {
        "email": unique_email(),
        "password": "StrongPass123",
        "display_name": "First Customer",
        "phone": phone,
    }
    second_payload = {
        "email": unique_email(),
        "password": "StrongPass123",
        "display_name": "Second Customer",
        "phone": phone,
    }

    first_response = client.post("/customers/register", json=first_payload)
    second_response = client.post("/customers/register", json=second_payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "customer_phone_already_registered"}


def test_customer_login_rejects_wrong_password() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Test Customer",
            "phone": None,
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/customers/login",
        json={
            "email": email,
            "password": "WrongPass123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "invalid_customer_credentials"}


def test_customer_register_and_login_with_phone_password() -> None:
    client = TestClient(app)
    phone = unique_phone()

    register_response = client.post(
        "/customers/register",
        json={
            "email": None,
            "password": "StrongPass123",
            "display_name": "Phone Customer",
            "phone": phone,
        },
    )

    assert register_response.status_code == 201

    register_payload = register_response.json()
    assert register_payload["token_type"] == "Bearer"
    assert register_payload["access_token"]
    assert register_payload["customer"]["email"] is None
    assert register_payload["customer"]["phone"] == phone
    assert register_payload["customer"]["display_name"] == "Phone Customer"

    login_response = client.post(
        "/customers/login",
        json={
            "phone": phone,
            "password": "StrongPass123",
        },
    )

    assert login_response.status_code == 200

    login_payload = login_response.json()
    assert login_payload["token_type"] == "Bearer"
    assert login_payload["access_token"]
    assert login_payload["customer"]["phone"] == phone
    assert login_payload["customer"]["last_login_at"] is not None


def test_customer_login_rejects_unknown_phone() -> None:
    client = TestClient(app)

    login_response = client.post(
        "/customers/login",
        json={
            "phone": unique_phone(),
            "password": "StrongPass123",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json() == {"detail": "invalid_customer_credentials"}


def test_customer_register_requires_email_or_phone() -> None:
    client = TestClient(app)

    register_response = client.post(
        "/customers/register",
        json={
            "email": None,
            "phone": None,
            "password": "StrongPass123",
            "display_name": "Missing Identifier",
        },
    )

    assert register_response.status_code == 422
