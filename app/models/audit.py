from sqlalchemy import Column, String, JSON, ForeignKey, select, and_, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from typing import Dict, Any, List, Optional
from app.db.base import TimestampedBase
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuditLog(TimestampedBase):
    __tablename__ = "audit_logs"

    entity_type = Column(String, nullable=False)  # workspace, user, team, task
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # create, update, delete
    changes = Column(JSON)  # Before/After states
    event_metadata = Column(JSON)  # IP, device info

    # Relationships
    actor = relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.id} - {self.action} on {self.entity_type}>"

    @classmethod
    async def log_action(
        cls,
        db_session,
        entity_type: str,
        entity_id: UUID,
        actor_id: UUID,
        action: str,
        changes: Dict[str, Any],
        event_metadata: Optional[Dict[str, Any]] = None
    ) -> "AuditLog":
        """
        Create an audit log entry
        
        Args:
            db_session: Database session
            entity_type: Type of entity being audited (e.g., "user", "task")
            entity_id: ID of the entity
            actor_id: ID of the user performing the action
            action: Type of action (create, update, delete)
            changes: Dictionary of changes made
            event_metadata: Additional event_metadata about the action
        
        Returns:
            AuditLog: Created audit log entry
        """
        try:
            audit_log = cls(
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                action=action,
                changes=changes,
                event_metadata=event_metadata or {}
            )
            
            db_session.add(audit_log)
            await db_session.commit()
            await db_session.refresh(audit_log)
            
            logger.info(
                "Audit log created",
                entity_type=entity_type,
                entity_id=str(entity_id),
                action=action,
                actor_id=str(actor_id)
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(
                "Failed to create audit log",
                error=str(e),
                entity_type=entity_type,
                entity_id=str(entity_id),
                action=action
            )
            raise

    @classmethod
    async def get_entity_history(
        cls,
        db_session,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100,
        skip: int = 0
    ) -> List["AuditLog"]:
        """
        Get the audit history for a specific entity
        
        Args:
            db_session: Database session
            entity_type: Type of entity
            entity_id: ID of the entity
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            List[AuditLog]: List of audit log entries
        """
        try:
            query = select(cls).where(
                and_(
                    cls.entity_type == entity_type,
                    cls.entity_id == entity_id
                )
            ).order_by(desc(cls.created_at)).offset(skip).limit(limit)
            
            result = await db_session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(
                "Failed to get entity history",
                error=str(e),
                entity_type=entity_type,
                entity_id=str(entity_id)
            )
            raise

    @classmethod
    async def get_actor_history(
        cls,
        db_session,
        actor_id: UUID,
        limit: int = 100,
        skip: int = 0
    ) -> List["AuditLog"]:
        """
        Get all actions performed by a specific user
        
        Args:
            db_session: Database session
            actor_id: ID of the user
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            List[AuditLog]: List of audit log entries
        """
        try:
            query = select(cls).where(
                cls.actor_id == actor_id
            ).order_by(desc(cls.created_at)).offset(skip).limit(limit)
            
            result = await db_session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(
                "Failed to get actor history",
                error=str(e),
                actor_id=str(actor_id)
            )
            raise