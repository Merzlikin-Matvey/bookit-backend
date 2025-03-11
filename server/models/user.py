import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from server.backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    login = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    sex = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    yandex_id = Column(String, nullable=True, unique=True)
    role = Column(String, default='user')
    verified = Column(Boolean, default=False)
    telegram_id = Column(String, nullable=True)
    avatar_id = Column(String, nullable=True)
