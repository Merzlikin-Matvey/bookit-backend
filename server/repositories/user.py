from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from server.models.user import User
from server.schemas.user import UserCreate


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    async def get_by_yandex_id(self, yandex_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.yandex_id == yandex_id))
        return result.scalars().first()

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        print("DATA", user_data)
        db_user = User(
            email=user_data.email,
            login=user_data.email,
            first_name=user_data.first_name,
            hashed_password=hashed_password,
            role=user_data.role
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def create_user_yandex(self, yandex_data: dict) -> User:
        email = yandex_data.get("default_email") or yandex_data.get("email")
        db_user = User(
            yandex_id=yandex_data.get("id"),
            email=email,
            login=email,
            first_name=yandex_data.get("first_name"),
            hashed_password=""
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update_user(self, user_id: UUID, update_data: dict) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()
        if not db_user:
            return None
        for field, value in update_data.items():
            setattr(db_user, field, value)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def delete_user(self, user_id: UUID) -> bool:
        result = await self.db.execute(select(User).filter(User.id == user_id))
        db_user = result.scalars().first()
        if not db_user:
            return False
        await self.db.delete(db_user)
        await self.db.commit()
        return True

    async def get_user_by_telegram(self, telegram_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.telegram_id == telegram_id))
        return result.scalars().first()

    async def get_all_admins(self):
        result = await self.db.execute(select(User).filter(User.role == "admin"))
        return result.scalars().all()
