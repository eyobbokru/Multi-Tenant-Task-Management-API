from typing import List
from uuid import UUID
from redis import Redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import  get_current_user
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    ChangePassword
)
from app.services.user import UserService
from app.models.user import User
from app.db.session import get_db
from app.db.redis import get_redis

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> UserResponse:
    """Create a new user."""
    user_service = UserService(db, redis)
    return await user_service.create_user(user_data)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Update current user information."""
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, user_data)

@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_current_user_password(
    password_data: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Change current user password."""
    user_service = UserService(db)
    await user_service.change_password(current_user.id, password_data)
    return {"message": "Password updated successfully"}

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get user by ID."""
    user_service = UserService(db)
    return await user_service.get_user(user_id)

@router.get("", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),

    # current_user: User = Depends(get_current_user)
) -> List[UserResponse]:
    """Get all users with pagination."""
    user_service = UserService(db, redis)
    return await user_service.get_users(skip=skip, limit=limit)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),

) -> None:
    """Delete user by ID."""
    user_service = UserService(db,redis)
    await user_service.delete_user(user_id)