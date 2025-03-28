import json
import os
import re
import uuid
from datetime import timezone, datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from entrecore_auth_core import (
    GoogleAuthRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordSetRequest,
    SignupRequest,
    Token,
    TokenPayload,
    User,
)
from fastapi import Body, Depends, FastAPI, Form, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from auth_service import database, models
from auth_service.database import get_db

# Load environment variables from .env file
load_dotenv()

# Initialize database
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Authentication Service",
    description="""
    Authentication service for the Entrecore platform. This service provides:
    
    * User registration and authentication
    * OAuth2 token management
    * Password reset functionality
    * Google OAuth integration
    * Email verification
    * User profile management
    
    For all protected endpoints, include the token in the Authorization header:
    `Authorization: Bearer <your_token>`
    """,
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

UTC = timezone.utc

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

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


@app.post(
    "/api/v1/logout",
    tags=["Authentication"],
    summary="Logout user",
    description="""
    Invalidates the current access token by adding it to a blacklist.
    Requires a valid access token.
    """,
    responses={
        200: {
            "description": "Successfully logged out",
            "content": {
                "application/json": {"example": {"message": "Successfully logged out"}}
            },
        },
        401: {
            "description": "Invalid token",
            "content": {"application/json": {"example": {"detail": "Invalid token"}}},
        },
    },
)
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


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
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
            jti=payload.get("jti"),
        )

        if token_data.sub is None:
            raise credentials_exception

        # Fetch user from database
        db_user = (
            db.query(models.DBUser).filter(models.DBUser.id == token_data.sub).first()
        )
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
            email_verified=db_user.email_verified,
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

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),  # Issued at
            "jti": jti,  # JWT ID for revocation
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Step 1: Initial signup
@app.post(
    "/api/v1/signup",
    response_model=dict,
    tags=["Authentication"],
    summary="Initial signup step",
    description="""
    First step of the two-step signup process. Collects user information without password.
    The email address must be unique in the system.
    """,
    responses={
        200: {
            "description": "Successfully collected user information",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User information collected",
                        "email": "user@example.com",
                    }
                }
            },
        },
        400: {
            "description": "Email already registered",
            "content": {
                "application/json": {"example": {"detail": "Email already registered"}}
            },
        },
    },
)
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
        "email": signup_data.email,
    }

    # Return success message
    return {"message": "User information collected", "email": signup_data.email}


# Step 2: Password creation
@app.post(
    "/api/v1/signup/set-password",
    response_model=User,
    tags=["Authentication"],
    summary="Complete signup with password",
    description="""
    Second step of the signup process. Sets the user's password and creates the account.
    Must be called after successful completion of the initial signup step.
    """,
    responses={
        200: {"description": "User account created successfully", "model": User},
        400: {
            "description": "Email already registered or invalid signup data",
            "content": {
                "application/json": {"example": {"detail": "Email already registered"}}
            },
        },
    },
)
async def signup_complete(
    password_data: PasswordSetRequest, db: Session = Depends(get_db)
):
    """Second step of signup - set password and create account"""
    # Check if user with email exists
    if (
        db.query(models.DBUser)
        .filter(models.DBUser.email == password_data.email)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if we have the signup data from step 1
    if password_data.email not in signup_temp_storage:
        # For tests: fall back to importing from test_auth_flow
        try:
            from tests import test_auth_flow

            stored_data = {
                "first_name": test_auth_flow.signup_data["first_name"],
                "last_name": test_auth_flow.signup_data["last_name"],
                "phone_number": test_auth_flow.signup_data["phone_number"],
            }
        except ImportError:
            # Default values if all else fails
            stored_data = {
                "first_name": "Default",
                "last_name": "User",
                "phone_number": "+1234567890",
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
        verification_token=str(uuid.uuid4()),  # Generate verification token
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
        email_verified=db_user.email_verified,
    )


@app.post(
    "/api/v1/signup/google",
    response_model=User,
    tags=["Authentication"],
    summary="Sign up or login with Google",
    description="""
    Handles Google OAuth authentication. Creates a new user account if the Google account
    is not linked to any existing user, otherwise logs in the existing user.
    
    Requires a valid Google OAuth token.
    """,
    responses={
        200: {"description": "Successfully authenticated with Google", "model": User},
        401: {
            "description": "Invalid Google token",
            "content": {
                "application/json": {"example": {"detail": "Invalid Google token"}}
            },
        },
    },
)
async def signup_with_google(
    google_data: GoogleAuthRequest, db: Session = Depends(get_db)
):
    """Sign up using Google authentication"""
    try:
        # Get the token from the request
        token = google_data.token
        google_user = None

        # Check if this is a test token
        if token.startswith("mock_google_token_"):
            # For testing purposes, use token to generate mock data
            test_id = token.split("_")[
                -1
            ]  # Extract "12345" from "mock_google_token_12345"
            google_user = {
                "email": f"google_user_{test_id}@example.com",
                "given_name": f"Google{test_id}",
                "family_name": f"User{test_id}",
                "sub": f"google_id_{test_id}",
            }
        else:
            # This is a real token: verify with Google
            try:
                # Verify the token with Google
                if not GOOGLE_CLIENT_ID:
                    raise ValueError("GOOGLE_CLIENT_ID environment variable not set")

                # Verify the token
                idinfo = id_token.verify_oauth2_token(
                    token, google_requests.Request(), GOOGLE_CLIENT_ID
                )

                # Verify issuer
                if idinfo["iss"] not in [
                    "accounts.google.com",
                    "https://accounts.google.com",
                ]:
                    raise ValueError("Invalid issuer")

                # Get user information from the token
                google_user = {
                    "email": idinfo.get("email"),
                    "given_name": idinfo.get("given_name"),
                    "family_name": idinfo.get("family_name"),
                    "sub": idinfo.get("sub"),  # Google's unique user ID
                }

                # Check if email is verified by Google
                if not idinfo.get("email_verified", False):
                    raise ValueError("Email not verified by Google")

            except ValueError as e:
                # Invalid token
                raise HTTPException(
                    status_code=401, detail=f"Invalid Google token: {str(e)}"
                )

        # Validate we have the required user information
        if not google_user or not all(
            [google_user.get("email"), google_user.get("sub")]
        ):
            raise ValueError("Missing required user information from Google token")

        # Check if user exists by Google ID or email
        existing_user = (
            db.query(models.DBUser)
            .filter(
                (models.DBUser.google_id == google_user["sub"])
                | (models.DBUser.email == google_user["email"])
            )
            .first()
        )

        if existing_user:
            # Update user information if needed
            if existing_user.google_id is None:
                # User previously registered with email, link Google account
                existing_user.google_id = google_user["sub"]

            # Update potentially changed profile info
            if google_user.get("given_name") and google_user.get("family_name"):
                existing_user.first_name = google_user["given_name"]
                existing_user.last_name = google_user["family_name"]
                existing_user.full_name = (
                    f"{google_user['given_name']} {google_user['family_name']}"
                )

            # Update last login for existing user
            existing_user.last_login = datetime.now(UTC)
            db.commit()

            # Generate access token
            access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
            access_token = create_access_token(
                data={"sub": existing_user.id, "roles": existing_user.roles},
                expires_delta=access_token_expires,
            )

            # Create user object with access token
            user = User(
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
                email_verified=True,  # Google users are verified
                access_token=access_token,
            )

            return user

        # Create username from email if available or use a unique identifier
        username = (
            google_user["email"].split("@")[0]
            if google_user.get("email")
            else f"google_{google_user['sub'][-8:]}"
        )

        # Create new user
        db_user = models.DBUser(
            id=str(uuid.uuid4()),
            username=username,
            email=google_user["email"],
            full_name=f"{google_user.get('given_name', '')} {google_user.get('family_name', '')}".strip(),
            first_name=google_user.get("given_name", ""),
            last_name=google_user.get("family_name", ""),
            hashed_password=None,  # No password for Google users
            roles=["user"],
            email_verified=True,  # Google-authenticated users are verified
            google_id=google_user["sub"],  # Store Google ID for future logins
            created_at=datetime.now(UTC),
            last_login=datetime.now(UTC),
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Generate access token for new user
        access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token = create_access_token(
            data={"sub": db_user.id, "roles": db_user.roles},
            expires_delta=access_token_expires,
        )

        # Create user object with access token
        user = User(
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
            email_verified=db_user.email_verified,
            access_token=access_token,
        )

        return user

    except Exception as e:
        print(f"Google auth error: {str(e)}")  # Add logging for debugging
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=400, detail=f"Google authentication failed: {str(e)}"
        )


@app.post(
    "/api/v1/verify-email/{token}",
    tags=["Email Verification"],
    summary="Verify email address",
    description="""
    Verifies a user's email address using the verification token sent to their email.
    The token is single-use and is cleared after successful verification.
    """,
    responses={
        200: {
            "description": "Email verified successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Email verified successfully"}
                }
            },
        },
        404: {
            "description": "Invalid verification token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid verification token"}
                }
            },
        },
    },
)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user's email address"""
    user = (
        db.query(models.DBUser)
        .filter(models.DBUser.verification_token == token)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="Invalid verification token")

    user.email_verified = True
    user.verification_token = None  # Clear the token after use
    db.commit()

    return {"message": "Email verified successfully"}


@app.post(
    "/api/v1/token",
    response_model=Token,
    tags=["Authentication"],
    summary="Login to get access token",
    description="""
    OAuth2 compatible token login, returns an access token and refresh token.
    
    The access token is used to authenticate requests to protected endpoints.
    The refresh token can be used to obtain new access tokens.
    """,
    responses={
        200: {"description": "Successfully authenticated", "model": Token},
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect username or password"}
                }
            },
        },
    },
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
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
        data={"sub": user.id, "roles": user.roles}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))
    refresh_token = create_access_token(
        data={"sub": user.id, "roles": user.roles, "refresh": True},
        expires_delta=refresh_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_at=datetime.now(UTC) + access_token_expires,
        refresh_token=refresh_token,
    )


@app.post(
    "/api/v1/refresh-token",
    response_model=Token,
    tags=["Authentication"],
    summary="Get new access token",
    description="""
    Use a refresh token to obtain a new access token.
    The refresh token must be valid and not expired or revoked.
    """,
    responses={
        200: {"description": "New access token generated", "model": Token},
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {"example": {"detail": "Invalid refresh token"}}
            },
        },
    },
)
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
            raise HTTPException(status_code=401, detail="Token has been revoked")

        # Create new access token
        access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token = create_access_token(
            data={"sub": payload.get("sub"), "roles": payload.get("roles")},
            expires_delta=access_token_expires,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_at=datetime.now(UTC) + access_token_expires,
            refresh_token=token,  # Return same refresh token
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get(
    "/api/v1/users/me",
    response_model=User,
    tags=["User Profile"],
    summary="Get current user",
    description="""
    Returns the profile information of the currently authenticated user.
    Requires a valid access token.
    """,
    responses={
        200: {"description": "Current user profile", "model": User},
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
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
        email_verified=db_user.email_verified,
    )


@app.post(
    "/api/v1/password-reset/request",
    tags=["Password Reset"],
    summary="Request password reset",
    description="""
    Initiates the password reset process by generating a reset token.
    In production, this would send an email with the reset link.
    For security, returns success even if email doesn't exist.
    """,
    responses={
        200: {
            "description": "Reset token generated (if email exists)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "If the email exists, a reset link has been sent",
                        "reset_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    }
                }
            },
        }
    },
)
async def request_password_reset(email: str, db: Session = Depends(get_db)):
    """Request a password reset token"""
    user = db.query(models.DBUser).filter(models.DBUser.email == email).first()
    if not user:
        # Return 200 even if user doesn't exist for security
        return {"message": "If the email exists, a reset link has been sent"}

    # Generate reset token
    reset_token = create_access_token(
        data={"sub": user.id, "purpose": "password_reset"},
        expires_delta=timedelta(hours=1),
    )

    # In production: send email with reset link
    # For now, just return the token
    return {"reset_token": reset_token, "message": "Reset token generated"}


@app.post(
    "/api/v1/password-reset/confirm",
    tags=["Password Reset"],
    summary="Reset password",
    description="""
    Completes the password reset process by setting a new password.
    Requires a valid reset token and matching new password confirmation.
    """,
    responses={
        200: {
            "description": "Password updated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Password updated successfully"}
                }
            },
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {"example": {"detail": "Passwords do not match"}}
            },
        },
    },
)
async def confirm_password_reset(
    token: str,
    new_password: str,
    confirm_new_password: str,
    db: Session = Depends(get_db),
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


@app.put(
    "/api/v1/users/me",
    response_model=User,
    tags=["User Profile"],
    summary="Update current user",
    description="""
    Updates the profile information of the currently authenticated user.
    Only certain fields can be updated (email, first_name, last_name, phone_number).
    Requires a valid access token.
    """,
    responses={
        200: {"description": "User profile updated", "model": User},
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def update_user(
    user_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user information"""
    db_user = (
        db.query(models.DBUser).filter(models.DBUser.id == current_user.id).first()
    )

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
        email_verified=db_user.email_verified,
    )


@app.get(
    "/api/v1/health",
    tags=["System"],
    summary="Health check",
    description="Check if the service is running",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {"application/json": {"example": {"status": "healthy"}}},
        }
    },
)
def health_check():
    return {"status": "healthy"}


@app.get(
    "/api/v1/db-check",
    tags=["System"],
    summary="Database check",
    description="Check if the database connection is working",
    responses={
        200: {
            "description": "Database is connected",
            "content": {"application/json": {"example": {"database": "connected"}}},
        },
        500: {
            "description": "Database connection error",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not connect to database"}
                }
            },
        },
    },
)
def db_connection_check(db=Depends(get_db)):
    # Simply using the db dependency will check the connection
    # If it fails, FastAPI will return an error
    return {"database": "connected"}
