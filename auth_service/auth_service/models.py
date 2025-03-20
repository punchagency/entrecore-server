from sqlalchemy import Column, String, Boolean, DateTime, ARRAY
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime, UTC

class DBUser(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for Google users
    disabled = Column(Boolean, default=False)
    roles = Column(ARRAY(String), default=["user"])
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    last_login = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    google_id = Column(String, nullable=True) 