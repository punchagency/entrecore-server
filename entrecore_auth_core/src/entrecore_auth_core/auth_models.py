from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from datetime import datetime, UTC
import uuid
import re

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    full_name: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    disabled: bool = False
    roles: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_login: Optional[datetime] = None
    email_verified: bool = False
    verification_token: Optional[str] = None
    google_id: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    refresh_token: Optional[str] = None
    
class TokenPayload(BaseModel):
    sub: str  # user id
    exp: datetime
    roles: List[str]
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))  # unique token id

# Models for the two-step signup process
class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        # Basic phone number validation
        if not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v

class PasswordSetRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9@#$%^&*()_+\-=\[\]{};\':\\|,.<>\/?]', v):
            raise ValueError('Password must contain at least one number or special character')
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

# New models for Google auth
class GoogleAuthRequest(BaseModel):
    token: str

class GoogleUserInfo(BaseModel):
    email: EmailStr
    given_name: str
    family_name: str
    sub: str  # Google's unique identifier

# New models for password reset functionality
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    confirm_new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9@#$%^&*()_+\-=\[\]{};\':\\|,.<>\/?]', v):
            raise ValueError('Password must contain at least one number or special character')
        return v
    
    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

# For user profile updates
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None

# For email verification
class EmailVerification(BaseModel):
    token: str

# For more detailed role and permission management
class Permission(BaseModel):
    name: str
    description: Optional[str] = None

class Role(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

# For authentication response messages
class AuthMessage(BaseModel):
    message: str
    success: bool = True
    details: Optional[dict] = None
