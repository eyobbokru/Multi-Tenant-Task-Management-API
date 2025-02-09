from sqlalchemy import Column, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from app.db.base import TimestampedBase

class Comment(TimestampedBase):
    __tablename__ = "comments"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    attachments = Column(JSON)

    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")

    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"))  # For threaded comments

    parent = relationship(
        "Comment",
        back_populates="replies",
        remote_side="[Comment.id]",
        lazy="joined"
    )
    
    replies = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


    def __repr__(self):
        return f"<Comment {self.id} on {self.task_id}>"

class TimeEntry(TimestampedBase):
    __tablename__ = "time_entries"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    description = Column(Text)

    # Relationships
    task = relationship("Task", back_populates="time_entries")
    user = relationship("User", back_populates="time_entries")

    def __repr__(self):
        return f"<TimeEntry {self.id} for {self.task_id}>"