from sqlalchemy import Column, String, Text, Float, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import TimestampedBase

class Task(TimestampedBase):
    __tablename__ = "tasks"

    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False)  # backlog, todo, in_progress, review, done
    priority = Column(String, nullable=False)  # low, medium, high, urgent
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)
    meta_data = Column(JSON)  # Tags, custom fields
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    version = Column(Integer, default=1)  # For optimistic locking

    # Relationships
    team = relationship("Team", back_populates="tasks")
    creator = relationship("User", back_populates="created_tasks")
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="task", cascade="all, delete-orphan")
    parent = relationship("Task", remote_side=[id], backref="subtasks")

    def __repr__(self):
        return f"<Task {self.title}>"

class TaskAssignment(TimestampedBase):
    __tablename__ = "task_assignments"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # owner, assignee, reviewer

    # Relationships
    task = relationship("Task", back_populates="assignments")
    user = relationship("User", back_populates="task_assignments")

    def __repr__(self):
        return f"<TaskAssignment {self.task_id} - {self.user_id}>"