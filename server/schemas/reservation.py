from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ReservationStatusEnum(str, Enum):
    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"
    DID_NOT_COME = "did_not_come"


class ReservationBase(BaseModel):
    id: UUID
    user_id: UUID
    seat_id: UUID
    start: datetime
    end: datetime
    status: ReservationStatusEnum = ReservationStatusEnum.FUTURE
    model_config = ConfigDict(from_attributes=True)


class ReservationCreate(BaseModel):
    user_id: UUID
    seat_id: UUID
    start: datetime
    end: datetime
    model_config = ConfigDict(from_attributes=True)


class ReservationUpdate(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    status: Optional[ReservationStatusEnum] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReservationOut(ReservationBase):
    seat_name: str
    model_config = ConfigDict(from_attributes=True)
