from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

class APIKeyBase(BaseModel):
    name: str
    provider: str  # "gemini", "openai", etc.
    is_default: bool = False

class APIKeyCreate(APIKeyBase):
    api_key: str

class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    is_default: Optional[bool] = None
    status: Optional[APIKeyStatus] = None

class APIKey(APIKeyBase):
    id: str
    user_id: str
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class RegisterRequest(UserCreate):
    pass

class RegisterResponse(BaseModel):
    user: User
    message: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UserProfile(BaseModel):
    user: User
    api_keys: List[APIKey]
    stats: dict  # Usage statistics
