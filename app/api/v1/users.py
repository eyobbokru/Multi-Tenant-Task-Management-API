from typing import Dict, List
from uuid import UUID
from redis import Redis
from app.services.auth import AuthService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import  get_current_user
from app.schemas.user import (
    LoginResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
    ChangePassword
)
from app.services.user import UserService
from app.models.user import User
from app.db.session import get_db
from app.db.redis import get_redis
from fastapi.security import OAuth2PasswordRequestForm



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
    current_user: User = Depends(get_current_user),
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


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> LoginResponse:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    auth_service = AuthService(db, redis)
    tokens = await auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
        scope=form_data.scopes
    )
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return tokens

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
) -> Dict[str, str]:
    """
    Logout the current user by invalidating their tokens.
    """
    try:
        # Add the current token to the blacklist in Redis
        token_blacklist_key = f"blacklist:token:{current_user.id}"
        redis.sadd(token_blacklist_key, current_user.current_token)
        # Set expiration for blacklist key (e.g., 24 hours)
        redis.expire(token_blacklist_key, 86400)
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during logout"
        )