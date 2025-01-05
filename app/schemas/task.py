from datetime import datetime
from typing import Optional, Dict, List
from pydantic import Field
from uuid import UUID
from .base import BaseSchema, TimeStampedSchema, IDSchema

class TaskBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = Field(..., regex='^(backlog|todo|in_progress|review|done)$')
    priority: str = Field(..., regex='^(low|medium|high|urgent)$')
    parent_task_id: Optional[UUID] = None
    team_id: UUID
    creator_id: UUID
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict] = Field(default_factory=dict)
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, regex='^(backlog|todo|in_progress|review|done)$')
    priority: Optional[str] = Field(None, regex='^(low|medium|high|urgent)$')
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict] = None
    due_date: Optional[datetime] = None

class TaskInDB(TaskBase, TimeStampedSchema, IDSchema):
    completed_at: Optional[datetime] = None
    version: int = 1

class TaskResponse(TaskInDB):
    pass

class TaskAssignmentBase(BaseSchema):
    task_id: UUID
    user_id: UUID
    role: str = Field(..., regex='^(owner|assignee|reviewer)$')

class TaskAssignmentCreate(TaskAssignmentBase):
    pass

class TaskAssignmentUpdate(BaseSchema):
    role: str = Field(..., regex='^(owner|assignee|reviewer)$')

class TaskAssignmentInDB(TaskAssignmentBase, TimeStampedSchema, IDSchema):
    pass

class TaskAssignmentResponse(TaskAssignmentInDB):
    pass

class TimeEntryBase(BaseSchema):
    task_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    description: Optional[str] = None

class TimeEntryCreate(TimeEntryBase):
    pass

class TimeEntryUpdate(BaseSchema):
    end_time: datetime
    description: Optional[str] = None

class TimeEntryInDB(TimeEntryBase, TimeStampedSchema, IDSchema):
    pass

class TimeEntryResponse(TimeEntryInDB):
    pass

class CommentBase(BaseSchema):
    task_id: UUID
    user_id: UUID
    parent_id: Optional[UUID] = None
    content: str = Field(..., min_length=1)
    attachments: Optional[Dict] = Field(default_factory=dict)

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseSchema):
    content: str = Field(..., min_length=1)
    attachments: Optional[Dict] = None

class CommentInDB(CommentBase, TimeStampedSchema, IDSchema):
    pass

class CommentResponse(CommentInDB):
    pass

class TaskWithDetails(TaskResponse):
    assignments: List[TaskAssignmentResponse]
    time_entries: List[TimeEntryResponse]
    comments: List[CommentResponse]
    subtasks: List["TaskResponse"]