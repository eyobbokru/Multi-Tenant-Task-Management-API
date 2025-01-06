from redis import Redis
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.security import verify_password, SecurityUtils
from app.repositories.user import UserRepository
from app.schemas.user import LoginResponse
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.repository = UserRepository(session)
        self.redis = redis

    async def authenticate_user(
        self,
        email: str,
        password: str,
        scope: Optional[List[str]] = None
    ) -> Optional[LoginResponse]:
        """
        Authenticate user and return tokens if credentials are valid.
        """
        try:
            # Get user by email
            user = await self.repository.get_by_email(email)
           
            if not user:
                return None

            # Check if account is locked
            if await self._is_account_locked(user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is locked due to too many failed attempts"
                )

            # Verify password
            if not verify_password(password, user.password_hash):
                await self._record_failed_login(user.id)
                return None
           

          
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user"
                )
            
            

            # Clear failed login attempts on successful login
            await self._clear_failed_logins(user.id)
            
          
            # Update last login timestamp
            await self.repository.update_last_login(user.id)
            


            # Create tokens
            tokens = SecurityUtils.create_token_response(str(user.id))
                

            
            # Store refresh token in Redis for tracking
            refresh_token_key = f"refresh_token:{user.id}"
            self.redis.setex(
                refresh_token_key,
                86400 * 7,  # 7 days
                tokens["refresh_token"]
            )

            return LoginResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type="bearer"
            )

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )

    async def _is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked due to too many failed attempts."""
        key = f"failed_login:{user_id}"
        failed_attempts = self.redis.get(key)
        return int(failed_attempts or 0) >= 5  # Lock after 5 failed attempts

    async def _record_failed_login(self, user_id: str) -> None:
        """Record failed login attempt."""
        key = f"failed_login:{user_id}"
        self.redis.incr(key)
        self.redis.expire(key, 3600)

    async def _clear_failed_logins(self, user_id: str) -> None:
        """Clear failed login attempts."""
        key = f"failed_login:{user_id}"
        self.redis.delete(key)

    async def validate_token(self, token: str) -> bool:
        """
        Validate if token is in blacklist.
        """
        # Check if token is in blacklist
        return not self.redis.sismember("token_blacklist", token)