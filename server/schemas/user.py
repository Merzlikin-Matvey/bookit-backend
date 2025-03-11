from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr = Field(examples=["user1@example.com"])
    first_name: Optional[str] = Field(examples=["Test User"], default=None)
    role: Optional[str] = Field(examples=["user"], default="user")

class UserLogin(BaseModel):
    email: EmailStr = Field(examples=["demo_admin_0@example.com"])
    password: str = Field(examples=["password123"], min_length=8, max_length=20)

class UserCreate(UserBase):
    password: str = Field(examples=["userpass1234"], min_length=8, max_length=20)
    admin_key: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(examples=["user1@example.com"], default=None)
    first_name: Optional[str] = Field(examples=["Test User"], default=None)
    password: Optional[str] = Field(examples=["userpass1234"], default=None, min_length=8, max_length=20)
    role: Optional[str] = Field(examples=["user"], default=None)

class UserOut(UserBase):
    id: UUID
    verified: bool = False

    model_config = ConfigDict(from_attributes=True)

class UserUpdateAdmin(UserUpdate):
    verified: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserOut

class TokenData(BaseModel):
    sub: str
