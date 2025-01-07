import pytest
from fastapi.testclient import TestClient
from app.core.config import settings

# Test data
TEST_USER_DATA = {
    "email": "newuser@example.com",
    "name": "New User",
    "password": "Testpassword#123",
    "confirm_password": "Testpassword#123"
}

class TestUserAPI:
    def test_create_user(self, client: TestClient):
        response = client.post(
            f"{settings.API_V1_STR}/users",
            json=TEST_USER_DATA
        )
        print(response.json())
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == TEST_USER_DATA["email"]
        assert data["name"] == TEST_USER_DATA["name"]
        assert "id" in data
        assert "password" not in data

    def test_create_user_duplicate_email(self, client: TestClient):
        # Create first user
        response = client.post(
            f"{settings.API_V1_STR}/users",
            json=TEST_USER_DATA
        )
        assert response.status_code == 201

        # Try to create user with same email
        response = client.post(
            f"{settings.API_V1_STR}/users",
            json=TEST_USER_DATA
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_get_current_user(self, authorized_client: TestClient):
        response = authorized_client.get(f"{settings.API_V1_STR}/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "id" in data

    def test_update_current_user(self, authorized_client: TestClient):
        update_data = {
            "name": "Updated Name"
        }
        response = authorized_client.put(
            f"{settings.API_V1_STR}/users/me",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]

    def test_change_password(self, authorized_client: TestClient):
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
        response = authorized_client.post(
            f"{settings.API_V1_STR}/users/me/change-password",
            json=password_data
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"

    def test_change_password_wrong_current(self, authorized_client: TestClient):
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
        response = authorized_client.post(
            f"{settings.API_V1_STR}/users/me/change-password",
            json=password_data
        )
        assert response.status_code == 400
        assert "Incorrect password" in response.json()["detail"]

    def test_get_users(self, authorized_client: TestClient):
        response = authorized_client.get(f"{settings.API_V1_STR}/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_delete_user(self, authorized_client: TestClient):
        # First create a user to delete
        response = authorized_client.post(
            f"{settings.API_V1_STR}/users",
            json={
                "email": "todelete@example.com",
                "name": "To Delete",
                "password": "testpassword123",
                "confirm_password": "testpassword123"
            }
        )
        user_id = response.json()["id"]

        # Delete the user
        response = authorized_client.delete(
            f"{settings.API_V1_STR}/users/{user_id}"
        )
        assert response.status_code == 204

        # Try to get deleted user
        response = authorized_client.get(
            f"{settings.API_V1_STR}/users/{user_id}"
        )
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "invalid_data,expected_error",
        [
            (
                {
                    "email": "invalid-email",
                    "name": "Test User",
                    "password": "test123",
                    "confirm_password": "test123"
                },
                "value is not a valid email address"
            ),
            (
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "test",  # Too short
                    "confirm_password": "test"
                },
                "ensure this value has at least 8 characters"
            ),
            (
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "password": "test123",
                    "confirm_password": "different123"
                },
                "Passwords do not match"
            ),
        ]
    )
    def test_create_user_invalid_data(
        self,
        client: TestClient,
        invalid_data,
        expected_error
    ):
        response = client.post(
            f"{settings.API_V1_STR}/users",
            json=invalid_data
        )
        assert response.status_code in [400, 422]
        assert expected_error in str(response.json())

