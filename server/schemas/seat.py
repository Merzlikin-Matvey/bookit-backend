from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict

from uuid import UUID


class SeatBase(BaseModel):
    id: UUID
    name: str
    type: str
    x: float
    y: float
    has_computer: bool = False
    has_water: bool = False
    has_kitchen: bool = False
    has_smart_desk: bool = False
    is_quite: bool = False
    is_talk_room: bool = False

    is_available: bool = True


class SeatCreate(BaseModel):
    name: str
    type: str
    x: float
    y: float
    has_computer: bool = False
    has_water: bool = False
    has_kitchen: bool = False
    has_smart_desk: bool = False
    is_quite: bool = False
    is_talk_room: bool = False


class SeatUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    has_computer: Optional[bool] = None
    has_water: Optional[bool] = None
    has_kitchen: Optional[bool] = None
    has_smart_desk: Optional[bool] = None
    is_quite: Optional[bool] = None
    is_talk_room: Optional[bool] = None


class SeatOut(SeatBase):
    model_config = ConfigDict(from_attributes=True)
