import pytest
import jwt
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid

from server.services.auth import Auth
from server.services.auth import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS


@pytest.fixture
def auth_service():
    """Create an instance of the Auth service"""
    return Auth()


class TestAuth:
    def test_password_hashing(self, auth_service):
        """Test that password hashing works"""
        password = "testpassword123"
        hashed = auth_service.get_password_hash(password)
        
        # Check that the hash is not the same as the original password
        assert hashed != password
        
        # Check that the hash has the expected bcrypt format
        assert hashed.startswith("$2")
        assert len(hashed) > 50  # bcrypt hashes are typically longer than 50 chars

    def test_password_verification_success(self, auth_service):
        """Test that password verification works with correct password"""
        password = "testpassword123"
        hashed = auth_service.get_password_hash(password)
        
        # Verify the password against its hash
        assert auth_service.verify_password(password, hashed) is True

    def test_password_verification_failure(self, auth_service):
        """Test that password verification fails with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword123"
        hashed = auth_service.get_password_hash(password)
        
        # Verify the wrong password against the hash
        assert auth_service.verify_password(wrong_password, hashed) is False

    @patch("server.services.auth.os.environ")
    @patch("server.services.auth.jwt.encode")
    def test_get_jwt_secret(self, mock_encode, mock_environ, auth_service):
        """Test retrieving JWT secret from environment variable"""
        mock_environ.get.return_value = "test_secret"
        
        # Call the method that should access the environment variable
        secret = auth_service.get_jwt_secret()
        
        # Assert that the environment variable was accessed with the correct key
        mock_environ.get.assert_called_once_with("JWT_SECRET")
        
        # Assert that the correct secret was returned
        assert secret == "test_secret"

    @patch("server.services.auth.os.environ")
    def test_get_jwt_algorithm(self, mock_environ, auth_service):
        """Test retrieving JWT algorithm from environment variable"""
        mock_environ.get.return_value = "HS256"
        
        # Call the method that should access the environment variable
        algorithm = auth_service.get_jwt_algorithm()
        
        # Assert that the environment variable was accessed with the correct key
        mock_environ.get.assert_called_once_with("JWT_ALGORITHM")
        
        # Assert that the correct algorithm was returned
        assert algorithm == "HS256"

    @patch("server.services.auth.jwt.encode")
    def test_create_access_token_default_expiry(self, mock_encode, auth_service):
        """Test creating an access token with default expiration time"""
        # Setup
        user_id = uuid.uuid4()
        data = {"sub": user_id}
        mock_encode.return_value = "mocked_token"
        
        # Configure auth_service mocks
        auth_service.get_jwt_secret = MagicMock(return_value="test_secret")
        auth_service.get_jwt_algorithm = MagicMock(return_value="HS256")

        # Get current time to check expiry calculation
        now = datetime.utcnow()
        
        # Execute
        token = auth_service.create_access_token(data)
        
        # Assert
        assert token == "mocked_token"
        
        # Check that encode was called with correct parameters
        args, kwargs = mock_encode.call_args
        encoded_data = args[0]
        
        # Verify user ID was converted to string
        assert encoded_data["sub"] == str(user_id)
        
        # Verify expiration time - should be close to ACCESS_TOKEN_EXPIRE_MINUTES
        expiry_time = encoded_data["exp"]
        expected_expiry = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        delta = abs((expiry_time - expected_expiry).total_seconds())
        assert delta < 5  # Allow for slight time differences due to test execution
        
        # Verify that JWT encode was called with correct parameters
        mock_encode.assert_called_once_with(
            encoded_data, 
            auth_service.get_jwt_secret(), 
            algorithm=auth_service.get_jwt_algorithm()
        )

    @patch("server.services.auth.jwt.encode")
    def test_create_access_token_custom_expiry(self, mock_encode, auth_service):
        """Test creating an access token with custom expiration time"""
        # Setup
        user_id = uuid.uuid4()
        data = {"sub": user_id}
        custom_expiry = timedelta(hours=5)
        mock_encode.return_value = "mocked_token"
        
        # Configure auth_service mocks
        auth_service.get_jwt_secret = MagicMock(return_value="test_secret")
        auth_service.get_jwt_algorithm = MagicMock(return_value="HS256")
        
        # Get current time to check expiry calculation
        now = datetime.utcnow()
        
        # Execute
        token = auth_service.create_access_token(data, expires_delta=custom_expiry)
        
        # Assert
        assert token == "mocked_token"
        
        # Check that encode was called with correct parameters
        args, kwargs = mock_encode.call_args
        encoded_data = args[0]
        
        # Verify expiration time matches our custom value
        expiry_time = encoded_data["exp"]
        expected_expiry = now + custom_expiry
        delta = abs((expiry_time - expected_expiry).total_seconds())
        assert delta < 5  # Allow for slight time differences

    @patch("server.services.auth.jwt.encode")
    def test_create_refresh_token_default_expiry(self, mock_encode, auth_service):
        """Test creating a refresh token with default expiration time"""
        # Setup
        user_id = uuid.uuid4()
        data = {"sub": user_id}
        mock_encode.return_value = "mocked_refresh_token"
        
        # Configure auth_service mocks
        auth_service.get_jwt_secret = MagicMock(return_value="test_secret")
        auth_service.get_jwt_algorithm = MagicMock(return_value="HS256")
        
        # Get current time to check expiry calculation
        now = datetime.utcnow()
        
        # Execute
        token = auth_service.create_refresh_token(data)
        
        # Assert
        assert token == "mocked_refresh_token"
        
        # Check that encode was called with correct parameters
        args, kwargs = mock_encode.call_args
        encoded_data = args[0]
        
        # Verify user ID was converted to string
        assert encoded_data["sub"] == str(user_id)
        
        # Verify expiration time - should be close to REFRESH_TOKEN_EXPIRE_DAYS
        expiry_time = encoded_data["exp"]
        expected_expiry = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        delta = abs((expiry_time - expected_expiry).total_seconds())
        assert delta < 5  # Allow for slight time differences

    @patch("server.services.auth.jwt.encode")
    def test_create_refresh_token_custom_expiry(self, mock_encode, auth_service):
        """Test creating a refresh token with custom expiration time"""
        # Setup
        user_id = uuid.uuid4()
        data = {"sub": user_id}
        custom_expiry = timedelta(days=60)
        mock_encode.return_value = "mocked_refresh_token"
        
        # Configure auth_service mocks
        auth_service.get_jwt_secret = MagicMock(return_value="test_secret")
        auth_service.get_jwt_algorithm = MagicMock(return_value="HS256")
        
        # Get current time to check expiry calculation
        now = datetime.utcnow()
        
        # Execute
        token = auth_service.create_refresh_token(data, expires_delta=custom_expiry)
        
        # Assert
        assert token == "mocked_refresh_token"
        
        # Check that encode was called with correct parameters
        args, kwargs = mock_encode.call_args
        encoded_data = args[0]
        
        # Verify expiration time matches our custom value
        expiry_time = encoded_data["exp"]
        expected_expiry = now + custom_expiry
        delta = abs((expiry_time - expected_expiry).total_seconds())
        assert delta < 5  # Allow for slight time differences

    @patch("server.services.auth.jwt.encode")
    def test_data_conversion_in_token(self, mock_encode, auth_service):
        """Test that non-string data is properly converted in token creation"""
        # Setup various data types including UUID, int, and nested dict
        user_id = uuid.uuid4()
        complex_data = {
            "sub": user_id,
            "user_id": user_id,
            "count": 42,
            "nested": {"id": user_id}
        }
        mock_encode.return_value = "mocked_token"
        
        # Configure auth_service mocks
        auth_service.get_jwt_secret = MagicMock(return_value="test_secret")
        auth_service.get_jwt_algorithm = MagicMock(return_value="HS256")
        
        # Execute
        token = auth_service.create_access_token(complex_data)
        
        # Assert that token creation succeeded
        assert token == "mocked_token"
        
        # Check that sub was converted to string
        args, kwargs = mock_encode.call_args
        encoded_data = args[0]
        assert encoded_data["sub"] == str(user_id)
        
        # Other fields should remain unchanged
        assert encoded_data["user_id"] == user_id
        assert encoded_data["count"] == 42
        assert encoded_data["nested"]["id"] == user_id
