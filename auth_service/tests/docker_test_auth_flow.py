"""Docker-specific test for auth flow - runs inside container with Docker networking"""
import pytest
from fastapi.testclient import TestClient
from auth_service.main import app
import uuid
from datetime import datetime, timezone

# This test assumes it's running inside Docker with access to the 'db' service
client = TestClient(app)

def test_docker_health_check():
    """Verify basic API health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_docker_db_connection():
    """Test database connection in Docker environment"""
    # This assumes you have a DB connection check endpoint
    # If you don't have one, you could create a simple one
    response = client.get("/api/v1/db-check")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


