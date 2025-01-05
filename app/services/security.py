# app/services/security.py
from datetime import datetime, timedelta, timezone
import re
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis import Redis
from app.core.config import settings

class SecurityService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.password_attempt_expiry = 3600  # 1 hour
        self.max_login_attempts = 5

    async def validate_password_strength(self, password: str) -> None:
        """
        Validate password meets security requirements
        """
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        if not re.search(r"[A-Z]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter"
            )
            
        if not re.search(r"[a-z]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter"
            )
            
        if not re.search(r"\d", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number"
            )
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one special character"
            )

    async def check_password_history(self, user_id: UUID, new_password_hash: str) -> bool:
        """
        Check if password has been used recently
        """
        password_history_key = f"password_history:{user_id}"
        password_history = self.redis.lrange(password_history_key, 0, 4)  # Last 5 passwords
        return new_password_hash.encode() not in password_history

    async def add_to_password_history(self, user_id: UUID, password_hash: str) -> None:
        """
        Add password to history
        """
        password_history_key = f"password_history:{user_id}"
        self.redis.lpush(password_history_key, password_hash)
        self.redis.ltrim(password_history_key, 0, 4)  # Keep only last 5 passwords
        self.redis.expire(password_history_key, 180 * 24 * 3600)  # 180 days expiry

    async def record_failed_login(self, user_id: UUID) -> bool:
        """
        Record failed login attempt and check if account should be locked
        Returns True if account should be locked
        """
        key = f"failed_login:{user_id}"
        attempts = self.redis.incr(key)
        if attempts == 1:
            self.redis.expire(key, self.password_attempt_expiry)
        
        return attempts >= self.max_login_attempts

    async def clear_failed_logins(self, user_id: UUID) -> None:
        """
        Clear failed login attempts after successful login
        """
        key = f"failed_login:{user_id}"
        self.redis.delete(key)

    async def is_account_locked(self, user_id: UUID) -> bool:
        """
        Check if account is locked due to too many failed attempts
        """
        key = f"failed_login:{user_id}"
        attempts = self.redis.get(key)
        if attempts is None:
            return False
        return int(attempts) >= self.max_login_attempts

    async def enforce_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Implement rate limiting using sliding window
        """
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - window_seconds
        
        # Add the new request timestamp
        self.redis.zadd(key, {str(now): now})
        
        # Remove old entries outside the window
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count requests in the current window
        request_count = self.redis.zcount(key, window_start, float('inf'))
        
        # Set expiry on the key
        self.redis.expire(key, window_seconds)
        
        return request_count <= max_requests