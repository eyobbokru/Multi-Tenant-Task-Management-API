from typing import Optional, Dict, List
from pydantic import Field
from uuid import UUID
from .base import BaseSchema, TimeStampedSchema, IDSchema

class WorkspaceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[Dict] = Field(default_factory=dict)
    plan_type: str = "free"
    subscription_status: str = "active"

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[Dict] = None
    plan_type: Optional[str] = None
    subscription_status: Optional[str] = None

class WorkspaceInDB(WorkspaceBase, TimeStampedSchema, IDSchema):
    version: int = 1

class WorkspaceResponse(WorkspaceInDB):
    pass

class WorkspaceMemberBase(BaseSchema):
    workspace_id: UUID
    user_id: UUID
    role: str = Field(..., regex='^(owner|admin|member|guest)$')
    permissions: Optional[Dict] = Field(default_factory=dict)

class WorkspaceMemberCreate(WorkspaceMemberBase):
    pass

class WorkspaceMemberUpdate(BaseSchema):
    role: Optional[str] = Field(None, regex='^(owner|admin|member|guest)$')
    permissions: Optional[Dict] = None

class WorkspaceMemberInDB(WorkspaceMemberBase, TimeStampedSchema, IDSchema):
    pass

class WorkspaceMemberResponse(WorkspaceMemberInDB):
    pass

class WorkspaceWithMembers(WorkspaceResponse):
    members: List[WorkspaceMemberResponse]