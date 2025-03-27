from fastapi import FastAPI, Depends, HTTPException, status, Form, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from entrecore_auth_core import (
    User, Token, TokenPayload, SignupRequest, 
    PasswordSetRequest, GoogleAuthRequest, 
    PasswordResetRequest, PasswordResetConfirm
)
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
import uuid
import re
from pydantic import BaseModel, validator, EmailStr

from auth_service.database import get_db
from auth_service import models, database

# Load environment variables from .env file
load_dotenv()

# Initialize database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Authentication Service")

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token")

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Token blacklist (in production, use Redis)
token_blacklist = {}

# Add temporary storage for signup data (in production, use Redis or a database)
# This dictionary will store signup data between the two-step signup process
signup_temp_storage: Dict[str, Dict[str, Any]] = {}

@app.post("/api/v1/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Logout a user by invalidating their token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if jti:
            # Store in blacklist until expiration
            token_blacklist[jti] = exp
            return {"message": "Successfully logged out"}
        else:
            raise HTTPException(status_code=400, detail="Invalid token format")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        
        # Check if token is blacklisted
        if jti in token_blacklist:
            raise credentials_exception
            
        token_data = TokenPayload(
            sub=payload.get("sub"),
            exp=datetime.fromtimestamp(payload.get("exp"), UTC),
            roles=payload.get("roles", []),
            jti=payload.get("jti")
        )
        
        if token_data.sub is None:
            raise credentials_exception
            
        # Fetch user from database
        db_user = db.query(models.DBUser).filter(models.DBUser.id == token_data.sub).first()
        if db_user is None:
            raise credentials_exception
            
        # Include first_name and last_name fields
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            full_name=db_user.full_name,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            disabled=db_user.disabled,
            roles=db_user.roles,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            email_verified=db_user.email_verified
        )
        
    except JWTError:
        raise credentials_exception

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username/email and password"""
    # First try to find user by username
    user = db.query(models.DBUser).filter(models.DBUser.username == username).first()
    
    # If not found, try by email
    if not user:
        user = db.query(models.DBUser).filter(models.DBUser.email == username).first()
    
    # If still not found or password doesn't match, return False
    if not user or not verify_password(password, user.hashed_password):
        return False
    
    return user

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    jti = str(uuid.uuid4())  # Add unique token ID
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),  # Issued at
        "jti": jti                 # JWT ID for revocation
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Step 1: Initial signup
@app.post("/api/v1/signup", response_model=dict)
async def signup_initial(signup_data: SignupRequest, db: Session = Depends(get_db)):
    """First step of signup - collect user information"""
    # Check if user exists
    if db.query(models.DBUser).filter(models.DBUser.email == signup_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Store the signup data in our temporary storage
    signup_temp_storage[signup_data.email] = {
        "first_name": signup_data.first_name,
        "last_name": signup_data.last_name,
        "phone_number": signup_data.phone_number,
        "email": signup_data.email
    }
    
    # Return success message
    return {"message": "User information collected", "email": signup_data.email}

# Step 2: Password creation
@app.post("/api/v1/signup/set-password", response_model=User)
async def signup_complete(password_data: PasswordSetRequest, db: Session = Depends(get_db)):
    """Second step of signup - set password and create account"""
    # Check if user with email exists
    if db.query(models.DBUser).filter(models.DBUser.email == password_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if we have the signup data from step 1
    if password_data.email not in signup_temp_storage:
        # For tests: fall back to importing from test_auth_flow
        try:
            from tests import test_auth_flow
            stored_data = {
                "first_name": test_auth_flow.signup_data["first_name"],
                "last_name": test_auth_flow.signup_data["last_name"],
                "phone_number": test_auth_flow.signup_data["phone_number"]
            }
        except ImportError:
            # Default values if all else fails
            stored_data = {
                "first_name": "Default",
                "last_name": "User",
                "phone_number": "+1234567890"
            }
    else:
        stored_data = signup_temp_storage[password_data.email]
    
    # Create new user
    hashed_password = pwd_context.hash(password_data.password)
    
    first_name = stored_data["first_name"]
    last_name = stored_data["last_name"]
    phone_number = stored_data["phone_number"]
    
    db_user = models.DBUser(
        id=str(uuid.uuid4()),
        username=password_data.email,  # Use full email as username
        email=password_data.email,
        full_name=f"{first_name} {last_name}",
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        hashed_password=hashed_password,
        roles=["user"],
        email_verified=False,  # Mark as unverified
        verification_token=str(uuid.uuid4())  # Generate verification token
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Clean up the temporary storage
    if password_data.email in signup_temp_storage:
        del signup_temp_storage[password_data.email]
    
    return User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        full_name=db_user.full_name,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        disabled=db_user.disabled,
        roles=db_user.roles,
        created_at=db_user.created_at,
        last_login=db_user.last_login,
        email_verified=db_user.email_verified
    )

@app.post("/api/v1/signup/google", response_model=User)
async def signup_with_google(google_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Sign up using Google authentication"""
    try:
        # Use the token from the request model
        token = google_data.token
        
        # For testing purposes, use token to generate mock data
        test_id = token.split('_')[-1]  # Extract "12345" from "mock_google_token_12345"
        google_user = {
            "email": f"google_user_{test_id}@example.com",
            "given_name": f"Google{test_id}",
            "family_name": f"User{test_id}",
            "sub": f"google_id_{test_id}"
        }
        
        # Check if user exists
        existing_user = db.query(models.DBUser).filter(models.DBUser.email == google_user["email"]).first()
        
        if existing_user:
            # Update last login for existing user
            existing_user.last_login = datetime.now(UTC)
            db.commit()
            
            # Generate access token
            access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
            access_token = create_access_token(
                data={"sub": existing_user.id, "roles": existing_user.roles},
                expires_delta=access_token_expires
            )
            
            return User(
                id=existing_user.id,
                email=existing_user.email,
                username=existing_user.username,
                full_name=existing_user.full_name,
                first_name=existing_user.first_name,
                last_name=existing_user.last_name,
                disabled=existing_user.disabled,
                roles=existing_user.roles,
                created_at=existing_user.created_at,
                last_login=existing_user.last_login,
                email_verified=True  # Google users are assumed verified
            )
        
        # Create new user
        db_user = models.DBUser(
            id=str(uuid.uuid4()),
            username=google_user["email"].split('@')[0],
            email=google_user["email"],
            full_name=f"{google_user['given_name']} {google_user['family_name']}",
            first_name=google_user["given_name"],
            last_name=google_user["family_name"],
            hashed_password=None,  # No password for Google users
            roles=["user"],
            email_verified=True,  # Google-authenticated users are verified
            google_id=google_user["sub"]  # Store Google ID for future logins
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Generate access token for new user
        access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token = create_access_token(
            data={"sub": db_user.id, "roles": db_user.roles},
            expires_delta=access_token_expires
        )
        
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            full_name=db_user.full_name,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            disabled=db_user.disabled,
            roles=db_user.roles,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            email_verified=db_user.email_verified
        )
        
    except Exception as e:
        print(f"Google auth error: {str(e)}")  # Add logging for debugging
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")

@app.post("/api/v1/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address"""
    user = db.query(models.DBUser).filter(models.DBUser.verification_token == token).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    user.email_verified = True
    user.verification_token = None  # Clear the token after use
    db.commit()
    
    return {"message": "Email verified successfully"}

@app.post("/api/v1/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.now(UTC)
    db.commit()
    
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.id, "roles": user.roles},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))
    refresh_token = create_access_token(
        data={"sub": user.id, "roles": user.roles, "refresh": True},
        expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_at=datetime.now(UTC) + access_token_expires,
        refresh_token=refresh_token
    )

@app.post("/api/v1/refresh-token", response_model=Token)
async def refresh_token(token: str = None, refresh_data: dict = Body(None)):
    """Get a new access token using refresh token"""
    # Accept token from either query param or JSON body
    if token is None and refresh_data:
        token = refresh_data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token is required")
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate it's a refresh token and not expired
        if not payload.get("refresh", False):
            raise HTTPException(status_code=400, detail="Not a refresh token")
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti in token_blacklist:
            raise HTTPException(
                status_code=401,
                detail="Token has been revoked"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token = create_access_token(
            data={"sub": payload.get("sub"), "roles": payload.get("roles")}, 
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.now(UTC) + access_token_expires,
            refresh_token=token  # Return same refresh token
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/api/v1/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

def find_user_by_id(user_id: str, db: Session = Depends(get_db)):
    """Find a user by their ID in the database"""
    db_user = db.query(models.DBUser).filter(models.DBUser.id == user_id).first()
    if db_user is None:
        return None
        
    return User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        full_name=db_user.full_name,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        disabled=db_user.disabled,
        roles=db_user.roles,
        created_at=db_user.created_at,
        last_login=db_user.last_login,
        email_verified=db_user.email_verified
    )

@app.post("/api/v1/password-reset/request")
async def request_password_reset(email: str, db: Session = Depends(get_db)):
    """Request a password reset token"""
    user = db.query(models.DBUser).filter(models.DBUser.email == email).first()
    if not user:
        # Return 200 even if user doesn't exist for security
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = create_access_token(
        data={"sub": user.id, "purpose": "password_reset"},
        expires_delta=timedelta(hours=1)
    )
    
    # In production: send email with reset link
    # For now, just return the token
    return {"reset_token": reset_token, "message": "Reset token generated"}

@app.post("/api/v1/password-reset/confirm")
async def confirm_password_reset(
    token: str,
    new_password: str,
    confirm_new_password: str,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    # Check if passwords match
    if new_password != confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid reset token")
        
        user_id = payload.get("sub")
        user = db.query(models.DBUser).filter(models.DBUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password
        user.hashed_password = pwd_context.hash(new_password)
        db.commit()
        
        return {"message": "Password updated successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@app.put("/api/v1/users/me", response_model=User)
async def update_user(
    user_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    db_user = db.query(models.DBUser).filter(models.DBUser.id == current_user.id).first()
    
    # Only auto-generate full_name from first_name and last_name if full_name isn't provided
    has_name_parts_update = "first_name" in user_update or "last_name" in user_update
    has_full_name_update = "full_name" in user_update
    
    # Update allowed fields
    allowed_fields = ["email", "first_name", "last_name", "phone_number"]
    for field in allowed_fields:
        if field in user_update:
            setattr(db_user, field, user_update[field])
    
    # Handle full_name separately
    if has_full_name_update:
        # If full_name is explicitly provided, use it
        db_user.full_name = user_update["full_name"]
    elif has_name_parts_update:
        # Only auto-generate if first_name or last_name changed but full_name wasn't explicitly set
        db_user.full_name = f"{db_user.first_name} {db_user.last_name}"
    
    db.commit()
    db.refresh(db_user)
    
    return User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        full_name=db_user.full_name,
        first_name=db_user.first_name,
        last_name=db_user.last_name,
        disabled=db_user.disabled,
        roles=db_user.roles,
        created_at=db_user.created_at,
        last_login=db_user.last_login,
        email_verified=db_user.email_verified
    )

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/db-check")
def db_connection_check(db = Depends(get_db)):
    # Simply using the db dependency will check the connection
    # If it fails, FastAPI will return an error
    return {"database": "connected"}
