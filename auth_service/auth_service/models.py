from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
import uuid
from datetime import datetime, timezone
from .database import Base
from sqlalchemy.orm import validates


class DBUser(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, index=True, nullable=True)
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for Google users
    disabled = Column(Boolean, default=False)
    roles = Column(MySQLJSON, default=lambda: ["user"])
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login = Column(DateTime(timezone=True), nullable=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    google_id = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)

    @validates("roles")
    def validate_roles(self, key, roles):
        """Ensure roles is always stored as a list"""
        if roles is None:
            return ["user"]
        return roles

    def __repr__(self):
        return f"<DBUser(id={self.id}, username={self.username}, email={self.email})>"
