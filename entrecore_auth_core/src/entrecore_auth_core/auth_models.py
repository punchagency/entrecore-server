from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, UTC
import uuid

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    full_name: str
    disabled: bool = False
    roles: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_login: Optional[datetime] = None

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
