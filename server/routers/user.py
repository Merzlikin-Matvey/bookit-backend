from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.user import User
from server.schemas.user import UserOut, UserUpdate
from server.repositories.user import UserRepository
from server.backend.database import get_session
from server.services.auth import Auth
from server.dependencies.auth_dependencies import get_current_user_from_cookie

from uuid import UUID


router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserOut, summary="Получение данных текущего пользователя")
async def read_current_user(current_user: UserOut = Depends(get_current_user_from_cookie)):
    return current_user


@router.patch("", response_model=UserOut, summary="Редактирование пользователя")
async def update_user(
        user_update: UserUpdate,
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    user_repo = UserRepository(db)
    update_data = user_update.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = await user_repo.get_by_email(update_data["email"])
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = Auth().get_password_hash(update_data["password"])
        del update_data["password"]

    updated_user = await user_repo.update_user(current_user.id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return updated_user


@router.delete("", status_code=204, summary="Удаление пользователя")
async def delete_user(
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    user_repo = UserRepository(db)
    success = await user_repo.delete_user(current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return Response(status_code=204)


@router.get("/{user_id}", response_model=UserOut, summary="Получение данных пользователя по id")
async def get_user_by_id(user_id: UUID,
                         db: AsyncSession = Depends(get_session)):
    user = await db.execute(select(User).where(User.id == user_id))
    user = user.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return user
