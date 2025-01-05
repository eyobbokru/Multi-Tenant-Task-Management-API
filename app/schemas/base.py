from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimeStampedSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime

class IDSchema(BaseSchema):
    id: UUID