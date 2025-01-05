# tests/test_services/test_user_service.py
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from app.services.user import UserService
from app.schemas.user import UserCreate, UserUpdate, ChangePassword
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException

@pytest.fixture
def user_service(db, redis):
    return UserService(db, redis)

@pytest.fixture
def user_data():
    return UserCreate(
        email="test@example.com",
        name="Test User",
        password="SecurePass123!",
        confirm_password="SecurePass123!",
        profile={"avatar": "default.jpg"},
        preferences={"theme": "dark"},
        two_factor_enabled=False
    )

@pytest.mark.asyncio
async def test_create_user_success(user_service, user_data):
    # Act
    user = await user_service.create_user(user_data)
    
    # Assert
    assert user.email == user_data.email
    assert user.name == user_data.name

@pytest.mark.asyncio
async def test_create_user_password_mismatch(user_service, user_data):
    # Arrange
    user_data.confirm_password = "DifferentPass123!"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await user_service.create_user(user_data)
    assert exc.value.status_code == 400
    assert "Passwords do not match" in exc.value.detail

@pytest.mark.asyncio
async def test_create_user_weak_password(user_service, user_data):
    # Arrange
    user_data.password = "weak"
    user_data.confirm_password = "weak"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        await user_service.create_user(user_data)
    assert exc.value.status_code == 400
    assert "Password must be at least 8 characters" in exc.value.detail

@pytest.mark.asyncio
async def test_change_password_success(user_service, user_data):
    # Arrange
    user = await user_service.create_user(user_data)
    password_data = ChangePassword(
        current_password="SecurePass123!",
        new_password="NewSecurePass123!",
        confirm_password="NewSecurePass123!"
    )
    
    # Act
    await user_service.change_password(user.id, password_data)
    
    # Assert
    updated_user = await user_service.get_user(user.id)
    assert verify_password("NewSecurePass123!", updated_user.password_hash)

@pytest.mark.asyncio
async def test_password_history(user_service, user_data):
    # Arrange
    user = await user_service.create_user(user_data)
    old_password = user_data.password
    
    # Act & Assert - Try to change to the same password
    password_data = ChangePassword(
        current_password=old_password,
        new_password=old_password,
        confirm_password=old_password
    )
    
    with pytest.raises(HTTPException) as exc:
        await user_service.change_password(user.id, password_data)
    assert exc.value.status_code == 400
    assert "Password has been used recently" in exc.value.detail

@pytest.mark.asyncio
async def test_rate_limit_password_change(user_service, user_data):
    # Arrange
    user = await user_service.create_user(user_data)
    password_data = ChangePassword(
        current_password="SecurePass123!",
        new_password="NewSecurePass123!",
        confirm_password="NewSecurePass123!"
    )
    
    # Act - Attempt multiple password changes
    for _ in range(5):
        try:
            await user_service.change_password(user.id, password_data)
        except HTTPException:
            pass
    
    # Assert - Next attempt should be rate limited
    with pytest.raises(HTTPException) as exc:
        await user_service.change_password(user.id, password_data)
    assert exc.value.status_code == 429
    assert "Too many password change attempts" in exc.value.detail

@pytest.mark.asyncio
async def test_bulk_update_users(user_service):
    # Arrange
    users = []
    for i in range(3):
        user_data = UserCreate(
            email=f"test{i}@example.com",
            name=f"Test User {i}",
            password="SecurePass123!",
            confirm_password="SecurePass123!",
            profile={"avatar": "default.jpg"},
            preferences={"theme": "dark"},
            two_factor_enabled=False
        )
        user = await user_service.create_user(user_data)
        users.append(user)
    
    updates = [
        {users[0].id: UserUpdate(name="Updated Name 0")},
        {users[1].id: UserUpdate(name="Updated Name 1")},
        {users[2].id: UserUpdate(name="Updated Name 2")}
    ]
    
    # Act
    updated_users = await user_service.bulk_update_users(updates)
    
    # Assert
    assert len(updated_users) == 3
    assert all(user.name.startswith("Updated Name") for user in updated_users)

# To run the tests:
# docker-compose exec api bash
# python -m pytest tests/test_services/test_user_service.py -v --cov=app.services.user