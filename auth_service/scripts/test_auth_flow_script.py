#!/usr/bin/env python3
import requests
import uuid
import json
import time
from datetime import datetime

# Config
API_BASE_URL = "http://localhost:8000"  # Change to your API's URL
VERBOSE = True  # Set to False for less output

# Test user
test_user = {
    "username": f"testuser_{uuid.uuid4().hex[:8]}",
    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
}

# Store tokens
tokens = {}

def log(message, data=None):
    if VERBOSE:
        print(f"\n=== {message} ===")
        if data:
            print(json.dumps(data, indent=2, default=str))

def test_register():
    log("REGISTERING USER", test_user)
    response = requests.post(
        f"{API_BASE_URL}/register",
        params=test_user
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Registration failed"
    return data

def test_login():
    log("LOGGING IN", {
        "username": test_user["username"],
        "password": test_user["password"]
    })
    response = requests.post(
        f"{API_BASE_URL}/token",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        }
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Login failed"
    
    tokens["access_token"] = data["access_token"]
    tokens["refresh_token"] = data["refresh_token"]
    return data

def test_get_profile():
    log("GETTING USER PROFILE")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = requests.get(
        f"{API_BASE_URL}/users/me",
        headers=headers
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Getting profile failed"
    return data

def test_refresh_token():
    log("REFRESHING TOKEN", {"refresh_token": tokens["refresh_token"]})
    response = requests.post(
        f"{API_BASE_URL}/refresh-token",
        json={"token": tokens["refresh_token"]}
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Token refresh failed"
    
    # Update access token
    tokens["access_token"] = data["access_token"]
    return data

def test_update_profile():
    log("UPDATING PROFILE", {"full_name": "Updated Test User"})
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = requests.put(
        f"{API_BASE_URL}/users/me",
        headers=headers,
        json={"full_name": "Updated Test User"}
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Profile update failed"
    return data

def test_password_reset():
    # Request reset
    log("REQUESTING PASSWORD RESET", {"email": test_user["email"]})
    response = requests.post(
        f"{API_BASE_URL}/password-reset/request",
        params={"email": test_user["email"]}
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Password reset request failed"
    
    reset_token = data["reset_token"]
    new_password = "NewSecurePassword123!"
    
    # Confirm reset
    log("CONFIRMING PASSWORD RESET", {
        "token": reset_token,
        "new_password": new_password
    })
    response = requests.post(
        f"{API_BASE_URL}/password-reset/confirm",
        params={
            "token": reset_token,
            "new_password": new_password
        }
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Password reset confirmation failed"
    
    # Update test user password
    test_user["password"] = new_password
    return data

def test_logout():
    log("LOGGING OUT")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = requests.post(
        f"{API_BASE_URL}/logout",
        headers=headers
    )
    data = response.json()
    log(f"RESPONSE (Status: {response.status_code})", data)
    assert response.status_code == 200, "Logout failed"
    
    # Verify token is invalidated
    log("VERIFYING TOKEN INVALIDATION")
    response = requests.get(
        f"{API_BASE_URL}/users/me",
        headers=headers
    )
    log(f"RESPONSE (Status: {response.status_code})", response.json() if response.status_code < 300 else response.text)
    assert response.status_code == 401, "Token still valid after logout"
    return data

def run_all_tests():
    try:
        print("\n🔐 AUTHENTICATION API TEST FLOW 🔐")
        print("=" * 50)
        
        test_register()
        test_login()
        test_get_profile()
        test_refresh_token()
        test_update_profile()
        test_password_reset()
        # Login again with new password
        test_login()
        test_logout()
        
        print("\n✅ ALL TESTS PASSED SUCCESSFULLY! ✅")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    run_all_tests()