from entrecore_auth_core import User

def test_user_creation():
    user = User(email="test@example.com", username="testuser", full_name="Test User")
    assert user.email == "test@example.com"

