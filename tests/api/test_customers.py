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


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_customer_me_returns_current_customer() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Me Customer",
            "phone": None,
        },
    )

    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    me_response = client.get("/customers/me", headers=auth_headers(access_token))

    assert me_response.status_code == 200
    assert me_response.json()["email"] == email
    assert me_response.json()["display_name"] == "Me Customer"


def test_customer_me_requires_valid_session() -> None:
    client = TestClient(app)

    missing_response = client.get("/customers/me")
    invalid_response = client.get("/customers/me", headers=auth_headers("invalid-token"))

    assert missing_response.status_code == 401
    assert missing_response.json() == {"detail": "customer_auth_required"}
    assert invalid_response.status_code == 401
    assert invalid_response.json() == {"detail": "customer_auth_required"}


def test_customer_logout_revokes_current_session() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Logout Customer",
            "phone": None,
        },
    )

    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    before_logout_response = client.get("/customers/me", headers=auth_headers(access_token))
    logout_response = client.post("/customers/logout", headers=auth_headers(access_token))
    after_logout_response = client.get("/customers/me", headers=auth_headers(access_token))

    assert before_logout_response.status_code == 200
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "ok"}
    assert after_logout_response.status_code == 401
    assert after_logout_response.json() == {"detail": "customer_auth_required"}


def test_customer_logout_requires_valid_session() -> None:
    client = TestClient(app)

    missing_response = client.post("/customers/logout")
    invalid_response = client.post("/customers/logout", headers=auth_headers("invalid-token"))

    assert missing_response.status_code == 401
    assert missing_response.json() == {"detail": "customer_auth_required"}
    assert invalid_response.status_code == 401
    assert invalid_response.json() == {"detail": "customer_auth_required"}


def test_customer_change_password_updates_login_password() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Password Customer",
            "phone": None,
        },
    )
    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    change_response = client.post(
        "/customers/change-password",
        json={
            "current_password": "StrongPass123",
            "new_password": "NewStrongPass123",
        },
        headers=auth_headers(access_token),
    )

    assert change_response.status_code == 200
    assert change_response.json() == {"status": "ok"}

    old_login_response = client.post(
        "/customers/login",
        json={
            "email": email,
            "password": "StrongPass123",
        },
    )
    new_login_response = client.post(
        "/customers/login",
        json={
            "email": email,
            "password": "NewStrongPass123",
        },
    )

    assert old_login_response.status_code == 401
    assert old_login_response.json() == {"detail": "invalid_customer_credentials"}
    assert new_login_response.status_code == 200
    assert new_login_response.json()["customer"]["email"] == email


def test_customer_change_password_rejects_missing_or_invalid_session() -> None:
    client = TestClient(app)

    missing_response = client.post(
        "/customers/change-password",
        json={
            "current_password": "StrongPass123",
            "new_password": "NewStrongPass123",
        },
    )
    invalid_response = client.post(
        "/customers/change-password",
        json={
            "current_password": "StrongPass123",
            "new_password": "NewStrongPass123",
        },
        headers=auth_headers("invalid-token"),
    )

    assert missing_response.status_code == 401
    assert missing_response.json() == {"detail": "customer_auth_required"}
    assert invalid_response.status_code == 401
    assert invalid_response.json() == {"detail": "customer_auth_required"}


def test_customer_change_password_rejects_wrong_current_password() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Wrong Current Password",
            "phone": None,
        },
    )
    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    response = client.post(
        "/customers/change-password",
        json={
            "current_password": "WrongPass123",
            "new_password": "NewStrongPass123",
        },
        headers=auth_headers(access_token),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "customer_current_password_invalid"}


def test_customer_change_password_rejects_same_password() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Same Password",
            "phone": None,
        },
    )
    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    response = client.post(
        "/customers/change-password",
        json={
            "current_password": "StrongPass123",
            "new_password": "StrongPass123",
        },
        headers=auth_headers(access_token),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "customer_password_same_as_old"}


def test_customer_change_password_rejects_short_new_password() -> None:
    client = TestClient(app)
    email = unique_email()

    register_response = client.post(
        "/customers/register",
        json={
            "email": email,
            "password": "StrongPass123",
            "display_name": "Short Password",
            "phone": None,
        },
    )
    assert register_response.status_code == 201

    access_token = register_response.json()["access_token"]

    response = client.post(
        "/customers/change-password",
        json={
            "current_password": "StrongPass123",
            "new_password": "short",
        },
        headers=auth_headers(access_token),
    )

    assert response.status_code == 422
