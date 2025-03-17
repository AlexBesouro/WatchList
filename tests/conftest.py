import pytest
from fastapi.testclient import TestClient
from app.main import my_app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import get_db
from app import models
from app.auth import create_access_token

SQLALCHEMY_DATABASE_URL = (f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@"
                           f"{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}_test")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

test_session_local = sessionmaker(autoflush=False, autocommit=False, bind=engine)

@pytest.fixture
def session():
    print("session runs")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = test_session_local()
    try:
        yield db
    finally:
        db.close()
@pytest.fixture
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    my_app.dependency_overrides[get_db] = override_get_db
    return TestClient(my_app)


@pytest.fixture(scope="function")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_user(client):
    print("test user runs")
    user_data = {"email": "email@gmail.com",
                 "password": "Password_1",
                 "first_name": "Alex",
                 "last_name": "Bla"
                 }

    res = client.post("/users", json=user_data)
    new_test_user = res.json()
    new_test_user["password"] = user_data["password"]
    return new_test_user
#
#
@pytest.fixture
def access_token(test_user):
    return create_access_token({"user_email": test_user["email"]})

@pytest.fixture
def authorized_client(client, access_token):
    client.headers = {**client.headers, "authorization": f"bearer {access_token}"}
    return client
