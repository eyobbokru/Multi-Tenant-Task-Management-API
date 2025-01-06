from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from .base import BaseSchema, TimeStampedSchema, IDSchema

class UserBase(BaseSchema):
    email: EmailStr
    name: str
    is_active: bool = True
    profile: Optional[Dict] = Field(default_factory=dict)
    preferences: Optional[Dict] = Field(default_factory=dict)
    two_factor_enabled: bool = False

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")

class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    profile: Optional[Dict] = None
    preferences: Optional[Dict] = None
    two_factor_enabled: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)
    last_login_at: Optional[datetime] = None

class UserInDB(UserBase, TimeStampedSchema, IDSchema):
    last_login_at: Optional[datetime] = None

class UserResponse(UserInDB):
    pass

class UserWithToken(UserResponse):
    access_token: str
    token_type: str = "bearer"

class ChangePassword(BaseSchema):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New passwords do not match")
        

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class Token(BaseModel):
    access_token: str
    token_type: str