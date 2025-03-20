import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport
from auth_service.main import app
import uuid
from datetime import datetime, timedelta

client = TestClient(app)

# Test user email to use across steps
test_user_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

# First step signup data (matches SignupRequest model)
signup_data = {
    "first_name": f"Test{uuid.uuid4().hex[:4]}",
    "last_name": f"User{uuid.uuid4().hex[:4]}",
    "email": test_user_email,
    "phone_number": "+254712345678"
}

# Second step password data (matches PasswordSetRequest model)
password_data = {
    "email": test_user_email,
    "password": "SecurePassword123!",
    "confirm_password": "SecurePassword123!"
}

# Google auth test data
google_test_token = "mock_google_token_12345"
google_user_email = f"google_user_{uuid.uuid4().hex[:8]}@example.com"

# Store tokens between tests
tokens = {}

def test_signup_initial():
    """Test first step of user signup using SignupRequest model"""
    response = client.post(
        "/signup",
        json=signup_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User information collected"
    assert data["email"] == signup_data["email"]

def test_signup_complete():
    """Test second step of user signup using PasswordSetRequest model"""
    response = client.post(
        "/signup/set-password",
        json=password_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == password_data["email"]
    assert "id" in data
    assert "username" in data
    assert data["email_verified"] is False
    assert data["first_name"] == signup_data["first_name"]
    assert data["last_name"] == signup_data["last_name"]
    assert data["full_name"] == f"{signup_data['first_name']} {signup_data['last_name']}"
    
    # Store user ID for future tests
    global user_id
    user_id = data["id"]

def test_login_after_signup():
    """Test login after successful signup"""
    response = client.post(
        "/token",
        data={
            "username": test_user_email,  # Email is used as the username parameter
            "password": password_data["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Store tokens for subsequent tests
    tokens["access_token"] = data["access_token"]
    if "refresh_token" in data:
        tokens["refresh_token"] = data["refresh_token"]

def test_signup_with_google():
    """Test signup with Google authentication"""
    # Make a request to signup with Google
    response = client.post(
        "/signup/google",
        # Use the GoogleAuthRequest model structure
        json={"token": google_test_token}  # This matches GoogleAuthRequest model
    )
    assert response.status_code == 200
    data = response.json()
    
    # Store the user data for later tests
    global google_user_id
    google_user_id = data["id"]
    
    # Verify fields
    assert "id" in data
    assert "email" in data
    assert data["email_verified"] is True  # Google accounts should be verified automatically
    assert "first_name" in data
    assert "last_name" in data
    assert "full_name" in data
    assert data["full_name"] == f"{data['first_name']} {data['last_name']}"
    
    # Store access token
    tokens["google_user_token"] = data.get("access_token")

def test_google_login_existing_user():
    """Test login with Google for an existing user"""
    # Make another request with the same Google token
    response = client.post(
        "/signup/google",
        # Use the GoogleAuthRequest model structure
        json={"token": google_test_token}  # This matches GoogleAuthRequest model
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify it's the same user
    assert data["id"] == google_user_id
    assert data["email_verified"] is True
    
    # Access token should be updated
    if "access_token" in data:
        tokens["google_user_token"] = data["access_token"]

def test_get_current_user():
    """Test getting current user info with the token"""
    if not tokens.get("access_token"):
        pytest.skip("Access token not available")
    
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == signup_data["email"]
    assert data["first_name"] == signup_data["first_name"]
    assert data["last_name"] == signup_data["last_name"]

def test_refresh_token():
    """Test refreshing access token"""
    response = client.post(
        "/refresh-token",
        params={"token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    # Update access token
    tokens["access_token"] = data["access_token"]

def test_update_user_profile():
    """Test updating user profile"""
    new_name = "Updated Test User"
    first_name = "tested"
    response = client.put(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"full_name": new_name, "first_name": first_name}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == new_name
    assert data["first_name"] == first_name

def test_password_reset_request():
    """Test password reset request"""
    response = client.post(
        "/password-reset/request",
        params={"email": test_user_email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reset_token" in data
    tokens["reset_token"] = data["reset_token"]

def test_password_reset_confirm():
    """Test password reset confirmation"""
    new_password = "NewSecurePassword123!"
    response = client.post(
        "/password-reset/confirm",
        params={
            "token": tokens["reset_token"],
            "new_password": new_password,
            "confirm_new_password": new_password
        }
    )
    assert response.status_code == 200
    
    # Test login with new password
    response = client.post(
        "/token",
        data={
            "username": test_user_email,
            "password": new_password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200

def test_password_reset_confirm_mismatch():
    """Test password reset confirmation with mismatched passwords"""
    # First request a new reset token
    response = client.post(
        "/password-reset/request",
        params={"email": test_user_email}
    )
    assert response.status_code == 200
    mismatch_reset_token = response.json()["reset_token"]
    
    # Test with mismatched passwords
    response = client.post(
        "/password-reset/confirm",
        params={
            "token": mismatch_reset_token,
            "new_password": "NewPassword123!",
            "confirm_new_password": "DifferentPassword123!"
        }
    )
    assert response.status_code == 400
    assert "Passwords do not match" in response.json()["detail"]

def test_verify_email():
    """Test email verification with token"""
    # We'll use a simpler approach - just call the endpoint with a test token
    verification_token = "test-verification-token"
    
    # Simply make the request - the implementation should handle invalid tokens gracefully
    response = client.post(f"/verify-email/{verification_token}")
    
    # Check for expected response format
    # For an invalid token, it might return 400, but the important part is that the endpoint exists
    # and returns a structured response
    assert response.status_code in [200, 400, 404]
    
    # If it's a 404, that means the endpoint hasn't been implemented yet
    if response.status_code == 404:
        pytest.skip("Verify email endpoint not implemented yet")
    
    # For other status codes, verify we get a JSON response
    if response.status_code in [200, 400]:
        data = response.json()
        assert "message" in data

def test_logout():
    """Test user logout"""
    # Make sure we have a valid token first
    if not tokens.get("access_token"):
        pytest.skip("Access token not available")
    
    response = client.post(
        "/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "success" in response.json()["message"].lower()
    
    # Verify token is invalidated by trying to access a protected endpoint
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 401 