import pytest

from app.auth import verify_token
from tests.conftest import USER


# --- 1. Exchanging credentials for a token ----------------------------------
def test_login_returns_a_usable_token(client, test_user):
    """The token names the user, and that name is what the private routes read."""
    response = client.post(
        "/login", json={"email": USER["email"], "password": USER["password"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert verify_token(body["access_token"])["user_email"] == USER["email"]


# --- 2. Credentials the API refuses -----------------------------------------
@pytest.mark.parametrize(
    "payload",
    [
        {"email": USER["email"], "password": "WrongPassword_1"},
        {"email": "nobody@example.com", "password": USER["password"]},
    ],
)
def test_bad_credentials_are_refused(client, test_user, payload):
    """A wrong password and an unknown email give the same answer, on purpose."""
    response = client.post("/login", json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# ------------
def test_a_forged_token_is_refused(client, test_user):
    """A token we did not sign never opens a private route."""
    forged = {"Authorization": "Bearer not.a.real.token"}

    assert client.get("/users/me", headers=forged).status_code == 401
