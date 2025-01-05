from typing import AsyncGenerator, Optional, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.config import settings
from app.core.security import verify_token
from app.db.session import get_db
from app.services.user import UserService
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scopes={
        "admin": "Full access to all resources",
        "user": "Regular user access",
        "workspace:read": "Read workspace data",
        "workspace:write": "Modify workspace data",
        "team:read": "Read team data",
        "team:write": "Modify team data",
    }
)


async def get_current_user(
    security_scopes: SecurityScopes,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Dependency for getting current authenticated user."""
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_scopes = payload.get("scopes", [])
        for scope in security_scopes.scopes:
            if scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": authenticate_value},
                )
    except JWTError:
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.get_user(UUID(user_id))
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Security(get_current_user, scopes=["user"])
) -> User:
    """Dependency for getting current active user with basic user scope."""
    return current_user

async def get_current_admin_user(
    current_user: User = Security(get_current_user, scopes=["admin"])
) -> User:
    """Dependency for getting current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_workspace_access(
    workspace_id: UUID,
    current_user: User = Security(get_current_user, scopes=["workspace:read"]),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Check if current user has access to workspace."""
    user_service = UserService(db)
    has_access = await user_service.check_workspace_access(current_user.id, workspace_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    return True

async def get_team_access(
    team_id: UUID,
    current_user: User = Security(get_current_user, scopes=["team:read"]),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Check if current user has access to team."""
    user_service = UserService(db)
    has_access = await user_service.check_team_access(current_user.id, team_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this team"
        )
    return True

def check_permissions(required_permissions: List[str]):
    """Decorator to check user permissions."""
    async def permission_checker(
        current_user: User = Security(get_current_user)
    ) -> bool:
        user_permissions = current_user.permissions or []
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        return True
    return permission_checker

async def validate_workspace_member(
    workspace_id: UUID,
    current_user: User = Security(get_current_user, scopes=["workspace:read"]),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Validate that current user is a member of the workspace."""
    user_service = UserService(db)
    is_member = await user_service.is_workspace_member(current_user.id, workspace_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this workspace"
        )
    return True

async def validate_team_member(
    team_id: UUID,
    current_user: User = Security(get_current_user, scopes=["team:read"]),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Validate that current user is a member of the team."""
    user_service = UserService(db)
    is_member = await user_service.is_team_member(current_user.id, team_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this team"
        )
    return True