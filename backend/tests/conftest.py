import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import create_access_token
from app.database import get_db
from app.main import my_app

# SQLite in memory: the suite runs with no Docker, no server and no test database
# to create. StaticPool keeps every connection pointed at the same memory image.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

test_session_local = sessionmaker(autoflush=False, autocommit=False, bind=engine)

USER = {
    "email": "alex@example.com",
    "password": "Password_1",
    "first_name": "Alex",
    "last_name": "Zhukov",
}

OTHER_USER = {
    "email": "mallory@example.com",
    "password": "Password_2",
    "first_name": "Mallory",
    "last_name": "Other",
}


@pytest.fixture
def session():
    """A fresh, empty schema for every test."""
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = test_session_local()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session):
    """A test client whose requests hit the test database instead of Postgres."""

    def override_get_db():
        yield session
        # No close() here: the fixture owns the session, and closing it after the
        # first request would break every later one in the same test.

    my_app.dependency_overrides[get_db] = override_get_db
    yield TestClient(my_app)
    # Cleared, not left behind: dependency_overrides lives on the app object,
    # which is shared by the whole session.
    my_app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    """A registered account, plus the plain password the test typed."""
    response = client.post("/users", json=USER)
    assert response.status_code == 201
    return {**response.json(), "password": USER["password"]}


@pytest.fixture
def other_user(client):
    """A second account, used to prove one user never sees another's rows."""
    response = client.post("/users", json=OTHER_USER)
    assert response.status_code == 201
    return {**response.json(), "password": OTHER_USER["password"]}


def bearer(email: str) -> dict[str, str]:
    """The Authorization header a signed-in browser would send for `email`."""
    return {"Authorization": f"Bearer {create_access_token({'user_email': email})}"}


@pytest.fixture
def authorized_client(client, test_user):
    """The same client, signed in as `test_user`."""
    client.headers = {**client.headers, **bearer(test_user["email"])}
    return client
