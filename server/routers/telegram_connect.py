from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from uuid import UUID

from server.dependencies.auth_dependencies import get_current_user_from_cookie
from server.schemas.telegram_connect import TelegramConnectRequest
from server.schemas.user import UserOut
from server.services.telegram_connect import TelegramConnect
from server.repositories.user import UserRepository
from server.backend.database import get_session

router = APIRouter(prefix="/telegram", tags=["telegram"])

@router.get("/get_token")
async def get_token(user: UserOut = Depends(get_current_user_from_cookie)):
    token = await TelegramConnect().get_token(user.id)
    if token:
        return {"token": token}
    raise HTTPException(status_code=500, detail="Token generation failed")

@router.post("/connect")
async def connect_telegram(data: TelegramConnectRequest, db=Depends(get_session)):
    service = TelegramConnect()
    user_id = await service.get_user_from_token(data.token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    user_repo = UserRepository(db)
    updated_user = await user_repo.update_user(UUID(user_id), {"telegram_id": data.telegram_id})
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "Telegram account connected", "telegram_id": data.telegram_id}

@router.get("/exists")
async def check_user_exists(telegram_id: str, db=Depends(get_session)):
    user = await UserRepository(db).get_user_by_telegram(telegram_id)
    if user:
        return {"exists": True, "user_id": str(user.id)}
    return {"exists": False}
