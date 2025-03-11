from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from typing import Optional


class TicketStatusEnum(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class TicketThemeEnum(str, Enum):
    FAILURE = "failure"
    WISH = "wish"
    OTHER = "other"


class TicketBase(BaseModel):
    id: UUID
    user_id: UUID
    reservation_id: Optional[UUID] = None
    theme: str
    message: str
    status: Optional[TicketStatusEnum] = "active"
    made_on: datetime = Field(default_factory=datetime.now)


class TicketCreate(BaseModel):
    theme: TicketThemeEnum = "other"
    message: str


class TicketStatusUpdate(BaseModel):
    status: str


class TicketOut(TicketBase):
    model_config = ConfigDict(from_attributes=True)
