from pydantic import BaseModel


class TelegramConnectRequest(BaseModel):
    token: str
    telegram_id: str
