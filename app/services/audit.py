from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, select, func, cast, String
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from app.models.audit import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)

class AuditService:
    @staticmethod
    async def get_entity_audit_trail(
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[AuditLog]:
        """
        Get audit trail for a specific entity with date filtering
        """
        try:
            query = select(AuditLog).where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id
                )
            )

            if start_date:
                query = query.where(AuditLog.created_at >= start_date)
            if end_date:
                query = query.where(AuditLog.created_at <= end_date)

            query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
            
            result = await db.execute(query)
            return result.scalars().all()
        
        except Exception as e:
            logger.error(
                "Error getting entity audit trail",
                error=str(e),
                entity_type=entity_type,
                entity_id=str(entity_id)
            )
            raise

    @staticmethod
    async def search_audit_logs(
        db: AsyncSession,
        search_term: str,
        entity_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action_types: Optional[List[str]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[AuditLog]:
        """
        Search audit logs with various filters
        
        Args:
            db: Database session
            search_term: Text to search for in changes and event_metadata
            entity_types: List of entity types to filter by
            start_date: Start date for filtering
            end_date: End date for filtering
            action_types: List of action types to filter by
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            List[AuditLog]: Matching audit log entries
        """
        try:
            # Base query
            query = select(AuditLog)
            
            # Build filter conditions
            conditions = []
            
            # Search term in changes and metadata
            if search_term:
                search_conditions = [
                    cast(AuditLog.changes, String).ilike(f"%{search_term}%"),
                    cast(AuditLog.event_metadata, String).ilike(f"%{search_term}%")
                ]
                conditions.append(or_(*search_conditions))
            
            # Entity types filter
            if entity_types:
                conditions.append(AuditLog.entity_type.in_(entity_types))
            
            # Date range filter
            if start_date:
                conditions.append(AuditLog.created_at >= start_date)
            if end_date:
                conditions.append(AuditLog.created_at <= end_date)
            
            # Action types filter
            if action_types:
                conditions.append(AuditLog.action.in_(action_types))
            
            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Order by creation date and apply pagination
            query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(
                "Error searching audit logs",
                error=str(e),
                search_term=search_term,
                entity_types=entity_types
            )
            raise

    @staticmethod
    async def get_audit_statistics(
        db: AsyncSession,
        days: int = 30,
        entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed statistics about audit activities
        
        Args:
            db: Database session
            days: Number of days to analyze
            entity_type: Optional entity type to filter by
            
        Returns:
            Dict containing various statistics about audit activities
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Base query conditions
            conditions = [AuditLog.created_at >= start_date]
            if entity_type:
                conditions.append(AuditLog.entity_type == entity_type)
            
            # Activity by action type
            action_query = select(
                AuditLog.action,
                func.count().label('count')
            ).where(and_(*conditions)).group_by(AuditLog.action)
            
            # Activity by entity type
            entity_query = select(
                AuditLog.entity_type,
                func.count().label('count')
            ).where(and_(*conditions)).group_by(AuditLog.entity_type)
            
            # Activity by user
            user_query = select(
                AuditLog.actor_id,
                func.count().label('count')
            ).where(and_(*conditions)).group_by(AuditLog.actor_id)
            
            # Daily activity
            daily_query = select(
                func.date_trunc('day', AuditLog.created_at).label('day'),
                func.count().label('count')
            ).where(and_(*conditions)).group_by(text('day'))
            
            # Execute all queries
            action_result = await db.execute(action_query)
            entity_result = await db.execute(entity_query)
            user_result = await db.execute(user_query)
            daily_result = await db.execute(daily_query)
            
            # Compile statistics
            statistics = {
                'total_actions': sum(row.count for row in action_result),
                'actions_by_type': {row.action: row.count for row in action_result},
                'actions_by_entity': {row.entity_type: row.count for row in entity_result},
                'most_active_users': [
                    {'user_id': row.actor_id, 'count': row.count}
                    for row in user_result
                ],
                'daily_activity': [
                    {'date': row.day, 'count': row.count}
                    for row in daily_result
                ]
            }
            
            return statistics
            
        except Exception as e:
            logger.error(
                "Error getting audit statistics",
                error=str(e),
                days=days,
                entity_type=entity_type
            )
            raise