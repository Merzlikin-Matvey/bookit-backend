import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from server.dependencies.auth_dependencies import get_current_user_from_cookie
from server.schemas.user import UserCreate, TokenResponse, UserLogin, UserOut
from server.repositories.user import UserRepository
from server.backend.database import get_session
from server.services.auth import Auth
from server.backend.redis import get_redis_client
from server.backend.metrics import user_registrations_total, user_logins_total

redis_client = get_redis_client(0)

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_TOKEN_EXPIRE_SECONDS = 3600  # 1 час
REFRESH_TOKEN_EXPIRE_SECONDS = 2592000  # 30 дней

ENV_TYPE = os.getenv("ENV_TYPE", "server")
ADMIN_KEY = os.getenv("ADMIN_KEY")

def set_token_cookies(response: Response, access_token: str, refresh_token: str):
    """Set access and refresh token cookies on the response"""
    is_production = ENV_TYPE.lower() == "server"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_SECONDS,
        expires=ACCESS_TOKEN_EXPIRE_SECONDS,
        path="/",
        secure=is_production,
        samesite="lax" if not is_production else "strict",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_SECONDS,
        expires=REFRESH_TOKEN_EXPIRE_SECONDS,
        path="/",
        secure=is_production,
        samesite="lax" if not is_production else "strict",
    )

@router.post("/register", response_model=TokenResponse, summary="Регистрация пользователя")
async def register(user: UserCreate, response: Response, db: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(db)
    if await user_repo.get_by_email(user.email):
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    if user.admin_key:
        if user.admin_key != ADMIN_KEY:
            user.role = "user"
        user.role = "admin"
    else:
        user.role = "user"

    hashed_password = Auth().get_password_hash(user.password)
    db_user = await user_repo.create_user(user, hashed_password)

    access_token = Auth().create_access_token(data={"sub": str(db_user.id)})
    refresh_token = Auth().create_refresh_token(data={"sub": str(db_user.id)})

    await redis_client.set(f"user:{db_user.id}:access_token", access_token, ex=ACCESS_TOKEN_EXPIRE_SECONDS)
    await redis_client.set(f"user:{db_user.id}:refresh_token", refresh_token, ex=REFRESH_TOKEN_EXPIRE_SECONDS)

    set_token_cookies(response, access_token, refresh_token)
    user_registrations_total.inc(1)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=db_user
    )



@router.post("/login", response_model=TokenResponse, summary="Авторизация пользователя")
async def login(user: UserLogin, response: Response, db: AsyncSession = Depends(get_session)):
    """
    Данные для входа простого пользователя (не админа):
    email: demo_email_0@example.com    password: password123

    Данные для входа админа, стоят по дефоолту, но все же:
    email: demo_admin_0@example.com    password: password123

    """
    user_repo = UserRepository(db)
    db_user = await user_repo.get_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Неверный email")
    if not db_user.hashed_password or not Auth().verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный пароль")

    access_token = Auth().create_access_token(data={"sub": str(db_user.id)})
    refresh_token = Auth().create_refresh_token(data={"sub": str(db_user.id)})
    print("Acces", access_token)
    print("Refresh", refresh_token)
    await redis_client.set(f"user:{db_user.id}:access_token", access_token, ex=ACCESS_TOKEN_EXPIRE_SECONDS)
    await redis_client.set(f"user:{db_user.id}:refresh_token", refresh_token, ex=REFRESH_TOKEN_EXPIRE_SECONDS)

    set_token_cookies(response, access_token, refresh_token)
    user_logins_total.inc(1)

    print("USER ID", db_user.id)
    print("Email", db_user.email)
    print("ROLE", db_user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=db_user
    )


@router.post("/refresh", response_model=TokenResponse, summary="Обновление токенов")
async def refresh_tokens(refresh_token: str, response: Response, db: AsyncSession = Depends(get_session)):
    try:
        payload = jwt.decode(
            refresh_token,
            os.getenv("JWT_SECRET"),
            algorithms=[os.getenv("JWT_ALGORITHM")]
        )
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Неверный refresh token")
        user_id = UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Неверный refresh token")

    user_repo = UserRepository(db)
    db_user = await user_repo.get_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    stored_refresh = await redis_client.get(f"user:{db_user.id}:refresh_token")
    if not stored_refresh or stored_refresh.decode() != refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token недействителен")

    new_access_token = Auth().create_access_token(data={"sub": str(db_user.id)})
    new_refresh_token = Auth().create_refresh_token(data={"sub": str(db_user.id)})

    await redis_client.set(f"user:{db_user.id}:access_token", new_access_token, ex=ACCESS_TOKEN_EXPIRE_SECONDS)
    await redis_client.set(f"user:{db_user.id}:refresh_token", new_refresh_token, ex=REFRESH_TOKEN_EXPIRE_SECONDS)

    set_token_cookies(response, new_access_token, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=db_user
    )

@router.post("/logout", summary="Выход пользователя из аккаунта")
async def logout(
    response: Response,
    user: UserOut = Depends(get_current_user_from_cookie)
):
    await redis_client.delete(f"user:{user.id}:access_token")
    await redis_client.delete(f"user:{user.id}:refresh_token")

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"detail": "Вы успешно вышли из аккаунта"}

