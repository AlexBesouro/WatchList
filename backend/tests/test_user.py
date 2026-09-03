import pytest
from app import schemas


def test_create_user(client):
    """Successful creation"""
    res = client.post("/users", json={"email": "email@gmail.com",
                                      "password": "Password_1",
                                      "first_name": "Alex",
                                      "last_name": "Bla"
                                      })
    new_user_res = schemas.UserResponse(**res.json())
    assert new_user_res.email == "email@gmail.com"
    assert res.status_code == 201


@pytest.mark.parametrize("data, status_code", [({"email": "EMAIL@gmail.com", "password": "password",
                                                 "first_name": "Alex", "last_name": "Bla"}, 400),
                                               ({"email": "emailgmail.com", "password": "Password_1",
                                                 "first_name": "Alex", "last_name": "Bla"}, 422),
                                               ({"email": "email@gmail.com", "password": "Password_1",
                                                 "first_name": None, "last_name": "Bla"}, 422),
                                               ({"email": "email@gmail.com", "password": "Password_1",
                                                 "first_name": "Alex", "last_name": None}, 422),
                                               ({"email": None, "password": "Password_1",
                                                 "first_name": None, "last_name": "Bla"}, 422),
                                               ({"email": "email@gmail.com", "password": None,
                                                 "first_name": "Alex", "last_name": None}, 422),
                                               ({"email": "email@gmail.com", "password": "Password_1",
                                                 "first_name": "Alex", "last_name": "Bla"}, 409)])
def test_create_user_failure(client, test_user, data, status_code):
    """Test user creation fails"""
    response = client.post("/users/", json=data)
    assert response.status_code == status_code


def test_update_user(authorized_client, test_user):
    """Successful user updating"""
    res = authorized_client.patch("/users", json={"email": "email@gmail.com",
                                      "password": "Password_3",
                                      "first_name": "Alex",
                                      "last_name": "BlaBla"
                                      })
    new_user_res = schemas.UserResponse(**res.json())
    assert new_user_res.email == "email@gmail.com"
    assert res.status_code == 200



