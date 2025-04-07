import os
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4
from server.services.auth import Auth

# Import the Auth class from the same package

# Test constants
TEST_PASSWORD = "secure_password123"
TEST_DATA = {"sub": "user_id_123"}
TEST_SECRET = "test_secret_key"
TEST_ALGORITHM = "HS256"


@pytest.fixture
def auth_service():
    """Fixture to provide an Auth instance with mocked environment variables"""
    with patch.dict(os.environ, {"JWT_SECRET": TEST_SECRET, "JWT_ALGORITHM": TEST_ALGORITHM}):
        return Auth()


class TestAuth:
    def test_get_password_hash(self, auth_service):
        """Test that password hashing works and produces a different hash"""
        hashed = auth_service.get_password_hash(TEST_PASSWORD)
        assert hashed != TEST_PASSWORD
        assert len(hashed) > 0

    def test_verify_password(self, auth_service):
        """Test password verification with correct and incorrect passwords"""
        hashed = auth_service.get_password_hash(TEST_PASSWORD)
        
        assert auth_service.verify_password(TEST_PASSWORD, hashed) is True
        
        assert auth_service.verify_password("wrong_password", hashed) is False

