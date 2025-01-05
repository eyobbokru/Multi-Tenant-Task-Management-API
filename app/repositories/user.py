#app/respositories/user.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def create(self, schema: UserCreate) -> User:
        """Override create method to handle password hashing"""
        db_obj = User(
            email=schema.email,
            name=schema.name,
            password_hash=get_password_hash(schema.password),
            profile=schema.profile,
            preferences=schema.preferences,
            two_factor_enabled=schema.two_factor_enabled
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, *, id: UUID, schema: UserUpdate, exclude_unset: bool = True) -> Optional[User]:
        """Override update method to handle password hashing"""
        update_data = schema.model_dump(exclude_unset=exclude_unset)
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
        return await super().update(id=id, schema=UserUpdate(**update_data), exclude_unset=exclude_unset)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get_by_attribute("email", email)

    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp"""
        await self.update(
            id=user_id,
            schema=UserUpdate(last_login_at=datetime.utcnow()),
            exclude_unset=False
        )

    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user by setting is_active to False"""
        result = await self.update(
            id=user_id,
            schema=UserUpdate(is_active=False),
            exclude_unset=False
        )
        return bool(result)