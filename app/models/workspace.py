from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import TimestampedBase

class Workspace(TimestampedBase):
    __tablename__ = "workspaces"

    name = Column(String, nullable=False)
    description = Column(String)
    settings = Column(JSON)  # Includes theme, features, limits
    plan_type = Column(String)
    subscription_status = Column(String)
    version = Column(Integer, default=1)  # For optimistic locking

    # Relationships
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workspace {self.name}>"

class WorkspaceMember(TimestampedBase):
    __tablename__ = "workspace_members"

    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # admin, member, guest
    permissions = Column(JSON)

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_memberships")

    def __repr__(self):
        return f"<WorkspaceMember {self.user_id} in {self.workspace_id}>"