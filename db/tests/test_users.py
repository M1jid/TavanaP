import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

import models
import schemas


class TestUsersAPI:
    """Test suite for Users API endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, async_client: AsyncClient):
        """Test getting all users when database is empty."""
        response = await async_client.get("/users")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, async_client: AsyncClient, sample_user):
        """Test getting a user by ID."""
        response = await async_client.get(f"/users?id={sample_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["username"] == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, async_client: AsyncClient, sample_user):
        """Test getting a user by username."""
        response = await async_client.get(f"/users?username={sample_user.username}")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sample_user.username

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, async_client: AsyncClient, sample_user):
        """Test getting a user by email."""
        response = await async_client.get(f"/users?email={sample_user.email}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user.email

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent user."""
        response = await async_client.get("/users?id=99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "User does not exist"

    @pytest.mark.asyncio
    async def test_create_user(self, async_client: AsyncClient):
        """Test creating a new user."""
        user_data = {
            "username": "new_test_user",
            "full_name": "New Test User",
            "email": "newtest@example.com",
            "hashed_password": "new_hashed_password_123",
            "disabled": False,
            "permissions": ["read", "write", "admin"],
            "history": [],
            "query_ids": [1, 2, 3, 4, 5]
        }
        
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, async_client: AsyncClient, sample_user):
        """Test creating a user with duplicate username."""
        user_data = {
            "username": sample_user.username,  # Duplicate username
            "full_name": "Duplicate User",
            "email": "duplicate@example.com",
            "hashed_password": "hashed_password_123",
            "disabled": False,
            "permissions": ["read"],
            "history": [],
            "query_ids": [1, 2, 3]
        }
        
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, async_client: AsyncClient, sample_user):
        """Test creating a user with duplicate email."""
        user_data = {
            "username": "different_username",
            "full_name": "Different User",
            "email": sample_user.email,  # Duplicate email
            "hashed_password": "hashed_password_123",
            "disabled": False,
            "permissions": ["read"],
            "history": [],
            "query_ids": [1, 2, 3]
        }
        
        response = await async_client.post("/users", json=user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user(self, async_client: AsyncClient, sample_user):
        """Test updating a user."""
        update_data = {
            "full_name": "Updated Test User",
            "email": "updated@example.com",
            "disabled": True,
            "permissions": ["read", "write", "admin", "delete"]
        }
        
        response = await async_client.put(f"/users?id={sample_user.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]
        assert data["disabled"] == update_data["disabled"]
        assert data["permissions"] == update_data["permissions"]

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent user."""
        update_data = {"full_name": "Updated User"}
        response = await async_client.put("/users?id=99999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "User does not exist"

    @pytest.mark.asyncio
    async def test_delete_user(self, async_client: AsyncClient, sample_user):
        """Test deleting a user."""
        response = await async_client.delete(f"/users?id={sample_user.id}")
        assert response.status_code == 200
        assert response.json() == "successfully deleted the user"

        # Verify it's actually deleted
        get_response = await async_client.get(f"/users?id={sample_user.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent user."""
        response = await async_client.delete("/users?id=99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "User does not exist"

    @pytest.mark.asyncio
    async def test_get_users_with_multiple_users(self, async_client: AsyncClient, db_session: Session):
        """Test getting all users when multiple exist."""
        # Create multiple users
        users_data = [
            {
                "username": "user1",
                "full_name": "User One",
                "email": "user1@example.com",
                "hashed_password": "hash1",
                "disabled": False,
                "permissions": ["read"],
                "history": [],
                "query_ids": [1, 2, 3]
            },
            {
                "username": "user2",
                "full_name": "User Two",
                "email": "user2@example.com",
                "hashed_password": "hash2",
                "disabled": False,
                "permissions": ["read", "write"],
                "history": [],
                "query_ids": [1, 2, 3, 4]
            },
            {
                "username": "user3",
                "full_name": "User Three",
                "email": "user3@example.com",
                "hashed_password": "hash3",
                "disabled": True,
                "permissions": ["read", "write", "admin"],
                "history": [],
                "query_ids": [1, 2, 3, 4, 5]
            }
        ]
        
        for user_data in users_data:
            user = models.User(**user_data)
            db_session.add(user)
        db_session.commit()
        
        response = await async_client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least the 3 we just created
        assert any(user["username"] == "user1" for user in data)
        assert any(user["username"] == "user2" for user in data)
        assert any(user["username"] == "user3" for user in data)

    @pytest.mark.asyncio
    async def test_get_users_by_disabled_status(self, async_client: AsyncClient, db_session: Session):
        """Test getting users filtered by disabled status."""
        # Create users with different disabled status
        users_data = [
            {
                "username": "active_user",
                "full_name": "Active User",
                "email": "active@example.com",
                "hashed_password": "hash1",
                "disabled": False,
                "permissions": ["read"],
                "history": [],
                "query_ids": [1, 2, 3]
            },
            {
                "username": "disabled_user",
                "full_name": "Disabled User",
                "email": "disabled@example.com",
                "hashed_password": "hash2",
                "disabled": True,
                "permissions": ["read"],
                "history": [],
                "query_ids": [1, 2, 3]
            }
        ]
        
        for user_data in users_data:
            user = models.User(**user_data)
            db_session.add(user)
        db_session.commit()
        
        # Test getting disabled users
        response = await async_client.get("/users?disabled=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least 1 disabled user
        assert all(user["disabled"] == True for user in data)
        
        # Test getting active users
        response = await async_client.get("/users?disabled=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # At least 1 active user
        assert all(user["disabled"] == False for user in data) 