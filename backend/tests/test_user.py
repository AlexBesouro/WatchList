import pytest

from app import schemas
from tests.conftest import USER


# --- 1. Creating an account -------------------------------------------------
def test_create_user(client):
    """The happy path: a 201 and the new user, without the password."""
    response = client.post("/users", json=USER)

    assert response.status_code == 201
    body = response.json()
    assert "password" not in body
    assert schemas.UserResponse(**body).email == USER["email"]


# --- 2. The password policy -------------------------------------------------
@pytest.mark.parametrize(
    "password, missing",
    [
        ("Pass_1", "8 characters"),
        ("password_1", "uppercase"),
        ("PASSWORD_1", "lowercase"),
        ("Password_", "digit"),
        ("Password1", "special character"),
    ],
)
def test_weak_password_is_refused(client, password, missing):
    """Each rule is enforced on its own, and the answer says which one failed."""
    response = client.post("/users", json={**USER, "password": password})

    assert response.status_code == 400
    assert missing in response.json()["detail"]


# --- 3. Bodies the API turns away -------------------------------------------
@pytest.mark.parametrize(
    "payload, expected",
    [
        ({**USER, "email": "not-an-email"}, 422),
        ({**USER, "first_name": None}, 422),
        ({"email": "a@b.com"}, 422),
    ],
)
def test_invalid_body_is_refused(client, payload, expected):
    """Pydantic answers 422 before the handler ever runs."""
    assert client.post("/users", json=payload).status_code == expected


# ------------
def test_duplicate_email_is_refused(client, test_user):
    """The unique index on email is what answers, not a lookup before the insert."""
    response = client.post("/users", json=USER)

    assert response.status_code == 409


# --- 4. Reading your own account --------------------------------------------
def test_me_returns_the_signed_in_user(authorized_client, test_user):
    """GET /users/me is how the front-end restores a session from a saved token."""
    response = authorized_client.get("/users/me")

    assert response.status_code == 200
    assert response.json()["email"] == test_user["email"]


# ------------
def test_me_without_a_token_is_refused(client):
    """The dependency answers before the handler body, so no user data is read."""
    assert client.get("/users/me").status_code == 401
