from datetime import datetime, timedelta
from typing import Any, Optional, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any]
) -> str:
    """
    Create JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify JWT token and return payload
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.JWTError:
        return None

def get_token_data(token: str) -> Optional[str]:
    """
    Get subject from token
    """
    payload = verify_token(token)
    if payload:
        return payload.get("sub")
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hashed password
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash password
    """
    return pwd_context.hash(password)

def is_token_expired(token: str) -> bool:
    """
    Check if token is expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        expiration = datetime.fromtimestamp(payload["exp"])
        return datetime.utcnow() >= expiration
    except jwt.JWTError:
        return True

class SecurityUtils:
    @staticmethod
    def create_token_response(user_id: str) -> dict:
        """
        Create both access and refresh tokens
        """
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[str]:
        """
        Create new access token from refresh token
        """
        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
            
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        return create_access_token(user_id)