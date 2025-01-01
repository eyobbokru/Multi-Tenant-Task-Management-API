from sqlalchemy import Column, String, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import TimestampedBase

class Team(TimestampedBase):
    __tablename__ = "teams"

    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    settings = Column(JSON)
    is_active = Column(Boolean, default=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="team", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])

    def __repr__(self):
        return f"<Team {self.name}>"

class TeamMember(TimestampedBase):
    __tablename__ = "team_members"

    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # admin, member, guest
    permissions = Column(JSON)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

    def __repr__(self):
        return f"<TeamMember {self.user_id} in {self.team_id}>"