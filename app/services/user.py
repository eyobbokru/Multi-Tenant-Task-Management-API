# app/services/user.py
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis

from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse, ChangePassword
from app.core.security import verify_password, get_password_hash
from app.services.security import SecurityService
from app.core.logging import get_logger
logger = get_logger(__name__)

class UserService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.repository = UserRepository(session)
        self.security = SecurityService(session, redis)
        self.redis = redis

    async def get_users(self, skip: int = 0, limit: int = 10) -> List[UserResponse]:
        """Retrieve a list of users with pagination."""
        try:
            users = await self.repository.list(skip=skip, limit=limit)
            return [UserResponse.model_validate(user) for user in users]
        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving users"
            )

    async def delete_user(self, user_id: UUID) -> None:
        """Delete a user by ID."""
        try:
            user = await self.repository.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            await self.repository.delete(id=user_id)
            logger.info(f"User deleted successfully: {user.email}")
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting user"
            )
   
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user with enhanced validation."""
        # Check if passwords match
        if user_data.password != user_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        # Validate password strength
        await self.security.validate_password_strength(user_data.password)

        # Check if user with email already exists
        if await self.repository.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        try:
            user = await self.repository.create(user_data)
            # Add password to history
            await self.security.add_to_password_history(
                user.id,
                user.password_hash
            )
            logger.info(f"User created successfully: {user.email}")
            return UserResponse.model_validate(user)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    async def change_password(self, user_id: UUID, password_data: ChangePassword) -> None:
        """Change user password with enhanced security."""
        # Rate limit check
        rate_limit_key = f"password_change:{user_id}"
        if not await self.security.enforce_rate_limit(rate_limit_key, 5, 3600):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password change attempts. Please try again later."
            )

        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(password_data.current_password, user.password_hash):
            await self.security.record_failed_login(user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )

        # Check if account is locked
        if await self.security.is_account_locked(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked due to too many failed attempts"
            )

        # Check if new passwords match
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match"
            )

        # Validate password strength
        await self.security.validate_password_strength(password_data.new_password)

        # Check password history
        new_password_hash = get_password_hash(password_data.new_password)
        if not await self.security.check_password_history(user_id, new_password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password has been used recently"
            )

        try:
            # Update password
            await self.repository.update(
                user_id,
                UserUpdate(password=password_data.new_password)
            )
            # Add to password history
            await self.security.add_to_password_history(user_id, new_password_hash)
            # Clear failed login attempts
            await self.security.clear_failed_logins(user_id)
            logger.info(f"Password changed successfully for user: {user.email}")
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            raise

    async def bulk_update_users(
        self,
        updates: List[Dict[UUID, UserUpdate]]
    ) -> List[UserResponse]:
        """Update multiple users efficiently."""
        try:
            updated_users = []
            for update_dict in updates:
                for user_id, update_data in update_dict.items():
                    updated_user = await self.repository.update(
                        id=user_id,
                        schema=update_data
                    )
                    if updated_user:
                        updated_users.append(
                            UserResponse.model_validate(updated_user)
                        )
            logger.info(f"Bulk update completed for {len(updated_users)} users")
            return updated_users
        except Exception as e:
            logger.error(f"Error in bulk update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error updating users: {str(e)}"
            )

    async def get_user_activity(self, user_id: UUID) -> Dict:
        """Get user activity metrics."""
        try:
            last_login = await self.repository.get_last_login(user_id)
            password_changes = await self.repository.get_password_change_count(user_id)
            login_attempts = int(self.redis.get(f"failed_login:{user_id}") or 0)
            
            return {
                "last_login": last_login,
                "password_changes_last_30_days": password_changes,
                "recent_failed_login_attempts": login_attempts
            }
        except Exception as e:
            logger.error(f"Error getting user activity: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user activity"
            )

    async def initiate_password_reset(self, email: str) -> None:
        """Initiate password reset process."""
        user = await self.repository.get_by_email(email)
        if not user:
            # Return success even if user not found to prevent email enumeration
            return

        # Rate limit check
        rate_limit_key = f"password_reset:{email}"
        if not await self.security.enforce_rate_limit(rate_limit_key, 3, 3600):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please try again later."
            )

        try:
            # Generate reset token
            reset_token = self._generate_reset_token()
            
            # Store token in Redis with expiration
            token_key = f"password_reset_token:{user.id}"
            self.redis.setex(token_key, 3600, reset_token)  # 1 hour expiry
            
            # TODO: Send email with reset token
            logger.info(f"Password reset initiated for user: {email}")
        except Exception as e:
            logger.error(f"Error initiating password reset: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing password reset request"
            )

    def _generate_reset_token(self) -> str:
        """Generate secure reset token."""
        import secrets
        return secrets.token_urlsafe(32)
    
    async def get_user(self, user_id: UUID) -> UserResponse:
        """Retrieve user by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse.model_validate(user)