from typing import Any
from datetime import datetime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

@as_declarative()
class Base:
    """
    Base class for all database models
    """
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

class TimestampedBase(Base):
    """
    Abstract base class that includes created_at and updated_at timestamps
    """
    __abstract__ = True

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

# Import all models here
from app.models.user import User  # noqa
from app.models.team import Team, TeamMember  # noqa
from app.models.task import Task ,TaskAssignment # noqa
from app.models.workspace import Workspace,WorkspaceMember  # noqa
from app.models.comment import Comment,TimeEntry  # noqa
from app.models.audit import AuditLog  # noqa
from app.models.misc import Session, Notification