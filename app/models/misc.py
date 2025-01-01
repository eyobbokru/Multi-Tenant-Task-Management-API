from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import TimestampedBase

class Session(TimestampedBase):
    __tablename__ = "sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False)
    session_data = Column(JSON)  # Device, IP, User-Agent
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session {self.id} for {self.user_id}>"

class Notification(TimestampedBase):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # task, mention, system
    title = Column(String, nullable=False)
    content = Column(Text)
    context = Column(JSON)  # Related entities
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} for {self.user_id}>"