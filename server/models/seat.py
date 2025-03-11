import uuid
from sqlalchemy import Column, Float, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from server.backend.database import Base

class Seat(Base):
    __tablename__ = "seats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    x = Column(Float)
    y = Column(Float)
    name = Column(String)
    type = Column(String)
    has_computer = Column(Boolean, default=False)
    has_water = Column(Boolean, default=False)
    has_kitchen = Column(Boolean, default=False)
    has_smart_desk = Column(Boolean, default=False)
    is_quite = Column(Boolean, default=False)
    is_talk_room = Column(Boolean, default=False)

    @property
    def is_available(self):
        return getattr(self, '_is_available', False)

    @is_available.setter
    def is_available(self, value):
        self._is_available = value