from entrecore_auth_core import (
    User,
    Token,
    TokenPayload,
    SignupRequest,
    PasswordSetRequest,
    GoogleAuthRequest,
    GoogleUserInfo,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserUpdate,
    EmailVerification,
    Permission,
    Role,
    AuthMessage
)
import pytest
from datetime import datetime, UTC
import uuid

def test_user_creation():
    user = User(
        email="test@example.com", 
        username="testuser", 
        full_name="Test User", 
        first_name="Test", 
        last_name="User"
    )
    assert user.email == "test@example.com"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email_verified is False

def test_signup_request():
    signup = SignupRequest(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone_number="+12345678901"
    )
    assert signup.first_name == "Jane"
    assert signup.last_name == "Doe"
    assert signup.email == "jane.doe@example.com"
    assert signup.phone_number == "+12345678901"

def test_invalid_phone_number():
    with pytest.raises(ValueError, match="Invalid phone number format"):
        SignupRequest(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            phone_number="invalid"
        )

def test_password_set_request_valid():
    pwd_request = PasswordSetRequest(
        email="test@example.com",
        password="SecurePass123!",
        confirm_password="SecurePass123!"
    )
    assert pwd_request.email == "test@example.com"
    assert pwd_request.password == "SecurePass123!"
    assert pwd_request.confirm_password == "SecurePass123!"

def test_password_validation():
    # Test too short
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        PasswordSetRequest(
            email="test@example.com",
            password="Short1",
            confirm_password="Short1"
        )
    
    # Test missing lowercase
    with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
        PasswordSetRequest(
            email="test@example.com",
            password="PASSWORD123!",
            confirm_password="PASSWORD123!"
        )
    
    # Test missing uppercase
    with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
        PasswordSetRequest(
            email="test@example.com",
            password="password123!",
            confirm_password="password123!"
        )
    
    # Test missing number/special character
    with pytest.raises(ValueError, match="Password must contain at least one number or special character"):
        PasswordSetRequest(
            email="test@example.com",
            password="PasswordOnly",
            confirm_password="PasswordOnly"
        )
    
    # Test password mismatch
    with pytest.raises(ValueError, match="Passwords do not match"):
        PasswordSetRequest(
            email="test@example.com",
            password="SecurePass123!",
            confirm_password="DifferentPass123!"
        )

def test_password_reset_confirm():
    reset = PasswordResetConfirm(
        token="some-valid-jwt-token",
        new_password="NewSecurePass123!",
        confirm_new_password="NewSecurePass123!"
    )
    assert reset.token == "some-valid-jwt-token"
    assert reset.new_password == "NewSecurePass123!"
    assert reset.confirm_new_password == "NewSecurePass123!"

def test_google_auth():
    google_req = GoogleAuthRequest(token="google-oauth-token")
    assert google_req.token == "google-oauth-token"
    
    google_info = GoogleUserInfo(
        email="google.user@example.com",
        given_name="Google",
        family_name="User",
        sub="google-user-id-12345"
    )
    assert google_info.email == "google.user@example.com"
    assert google_info.given_name == "Google"
    assert google_info.family_name == "User"
    assert google_info.sub == "google-user-id-12345"

# to run the test: poetry run pytest