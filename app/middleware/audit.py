from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
from uuid import UUID
from app.core.logging import get_logger
from app.models.audit import AuditLog
from app.core.security import get_current_user_from_token

logger = get_logger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        audit_paths: Dict[str, str] = None,
        exclude_paths: list = None
    ):
        """
        Initialize the audit middleware
        
        Args:
            app: The ASGI application
            audit_paths: Dictionary mapping paths to entity types
            exclude_paths: List of paths to exclude from auditing
        """
        super().__init__(app)
        self.audit_paths = audit_paths or {
            "/api/v1/users": "user",
            "/api/v1/teams": "team",
            "/api/v1/tasks": "task",
            "/api/v1/workspaces": "workspace"
        }
        self.exclude_paths = exclude_paths or [
            "/api/v1/auth",
            "/docs",
            "/openapi.json"
        ]
        
    async def should_audit(self, request: Request) -> bool:
        """
        Determine if the request should be audited
        """
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return False
            
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return False
            
        return any(path.startswith(audit_path) for audit_path in self.audit_paths)

    async def get_entity_type(self, path: str) -> str:
        """
        Get entity type from path
        """
        for audit_path, entity_type in self.audit_paths.items():
            if path.startswith(audit_path):
                return entity_type
        return "unknown"

    async def get_entity_id(self, path: str) -> UUID:
        """
        Extract entity ID from path
        """
        parts = path.split("/")
        for part in parts:
            try:
                return UUID(part)
            except ValueError:
                continue
        return None

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request and create audit log if necessary
        """
        if not await self.should_audit(request):
            return await call_next(request)

        # Get request body for auditing
        body = await request.body()
        request._body = body  # Save body for later use
        
        try:
            # Get current user
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            current_user = await get_current_user_from_token(token)
            
            if not current_user:
                return await call_next(request)

            # Process request
            response = await call_next(request)

            # Create audit log
            if response.status_code in [200, 201, 204]:
                entity_type = await self.get_entity_type(request.url.path)
                entity_id = await self.get_entity_id(request.url.path)
                
                if entity_id:
                    # Determine action type
                    action_map = {
                        "POST": "create",
                        "PUT": "update",
                        "PATCH": "update",
                        "DELETE": "delete"
                    }
                    action = action_map.get(request.method)

                    # Create changes dictionary
                    try:
                        body_json = json.loads(body)
                    except json.JSONDecodeError:
                        body_json = {}

                    changes = {
                        "request": body_json,
                        "method": request.method,
                        "path": request.url.path
                    }

                    # Create metadata
                    event_metadata = {
                        "ip": request.client.host,
                        "user_agent": request.headers.get("user-agent"),
                        "status_code": response.status_code
                    }

                    # Log the action
                    async with request.app.state.db() as session:
                        await AuditLog.log_action(
                            session,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            actor_id=current_user.id,
                            action=action,
                            changes=changes,
                            event_metadata=event_metadata
                        )

            return response

        except Exception as e:
            logger.error(
                "Error in audit middleware",
                error=str(e),
                path=request.url.path
            )
            return await call_next(request)