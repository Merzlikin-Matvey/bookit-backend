import datetime
import uuid
from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from server.backend.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    reservation_id = Column(UUID(as_uuid=True), nullable=True)
    seat_id = Column(UUID(as_uuid=True), ForeignKey("seats.id", ondelete="SET NULL"), nullable=True)
    seat_name = Column(String, nullable=True)
    theme = Column(String)
    message = Column(String)
    status = Column(String, default="active")

    made_on = Column(DateTime, default=datetime.datetime.now)
