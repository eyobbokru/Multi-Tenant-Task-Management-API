from typing import Optional, Dict, List
from pydantic import Field
from uuid import UUID
from .base import BaseSchema, TimeStampedSchema, IDSchema

class TeamBase(BaseSchema):
    workspace_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    owner_id: UUID
    settings: Optional[Dict] = Field(default_factory=dict)
    is_active: bool = True

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    owner_id: Optional[UUID] = None
    settings: Optional[Dict] = None
    is_active: Optional[bool] = None

class TeamInDB(TeamBase, TimeStampedSchema, IDSchema):
    pass

class TeamResponse(TeamInDB):
    pass

class TeamMemberBase(BaseSchema):
    team_id: UUID
    user_id: UUID
    role: str = Field(..., regex='^(admin|member|guest)$')
    permissions: Optional[Dict] = Field(default_factory=dict)

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberUpdate(BaseSchema):
    role: Optional[str] = Field(None, regex='^(admin|member|guest)$')
    permissions: Optional[Dict] = None

class TeamMemberInDB(TeamMemberBase, TimeStampedSchema, IDSchema):
    pass

class TeamMemberResponse(TeamMemberInDB):
    pass

class TeamWithMembers(TeamResponse):
    members: List[TeamMemberResponse]