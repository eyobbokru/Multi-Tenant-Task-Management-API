from typing import TypeVar, Generic, Type, Optional, List, Any, Dict, Union
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository providing default implementations of CRUD operations
    """
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get a record by ID
        """
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_attribute(self, attr: str, value: Any) -> Optional[ModelType]:
        """
        Get a record by a specific attribute
        """
        query = select(self.model).where(getattr(self.model, attr) == value)
        result = await self.db.execute(query)
        print("here***")
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None
    ) -> List[ModelType]:
        """
        Get list of records with optional filtering and ordering
        """
        query = select(self.model)

        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))

        # Apply ordering
        if order_by:
            for field in order_by:
                direction = "asc"
                if field.startswith("-"):
                    direction = "desc"
                    field = field[1:]
                if hasattr(self.model, field):
                    query = query.order_by(
                        getattr(getattr(self.model, field), direction)()
                    )

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, schema: CreateSchemaType) -> ModelType:
        """
        Create a new record
        """
        db_obj = self.model(**schema.model_dump(exclude_unset=True))
        self.db.add(db_obj)
        try:
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def bulk_create(self, schemas: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple records at once
        """
        db_objs = [self.model(**schema.model_dump(exclude_unset=True)) for schema in schemas]
        self.db.add_all(db_objs)
        try:
            await self.db.commit()
            for obj in db_objs:
                await self.db.refresh(obj)
            return db_objs
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def update(
        self,
        *,
        id: UUID,
        schema: UpdateSchemaType,
        exclude_unset: bool = True
    ) -> Optional[ModelType]:
        """
        Update a record by ID
        """
        update_data = schema.model_dump(exclude_unset=exclude_unset)
        if not update_data:
            return await self.get_by_id(id)

        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )

        try:
            result = await self.db.execute(query)
            await self.db.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def delete(self, *, id: UUID) -> bool:
        """
        Delete a record by ID
        Returns True if record was deleted, False if record was not found
        """
        query = (
            delete(self.model)
            .where(self.model.id == id)
            .returning(self.model.id)
        )
        try:
            result = await self.db.execute(query)
            await self.db.commit()
            return bool(result.scalar_one_or_none())
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def exists(self, **kwargs) -> bool:
        """
        Check if a record exists with the given attributes
        """
        conditions = [getattr(self.model, k) == v for k, v in kwargs.items()]
        query = select(self.model).where(and_(*conditions))
        result = await self.db.execute(query)
        return bool(result.scalar_one_or_none())

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count total number of records with optional filtering
        """
        query = select(self.model)
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        result = await self.db.execute(query)
        return len(result.scalars().all())