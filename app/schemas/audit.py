from datetime import datetime
from typing import Optional, Dict
from pydantic import Field
from uuid import UUID
from .base import BaseSchema, TimeStampedSchema, IDSchema

class AuditLogBase(BaseSchema):
    entity_type: str = Field(..., regex='^(workspace|user|team|task)$')
    entity_id: UUID
    actor_id: UUID
    action: str = Field(..., regex='^(create|update|delete)$')
    changes: Dict = Field(default_factory=dict)
    metadata: Optional[Dict] = Field(default_factory=dict)

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogInDB(AuditLogBase, TimeStampedSchema, IDSchema):
    pass

class AuditLogResponse(AuditLogInDB):
    pass

class NotificationBase(BaseSchema):
    user_id: UUID
    type: str = Field(..., regex='^(task|mention|system)$')
    title: str
    content: str
    context: Optional[Dict] = Field(default_factory=dict)
    is_read: bool = False

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseSchema):
    is_read: bool

class NotificationInDB(NotificationBase, TimeStampedSchema, IDSchema):
    read_at: Optional[datetime] = None

class NotificationResponse(NotificationInDB):
    pass