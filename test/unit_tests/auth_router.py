import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import os
import jwt
from datetime import datetime, timedelta

from fastapi import HTTPException
from server.routers.auth import router, register, login, refresh_tokens, logout  # Import the actual handler functions
from server.schemas.user import UserCreate, UserLogin
from server.models.user import User


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock(return_value=b"refresh_token")  # Default to valid token
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.first_name = "Test User"
    user.role = "user"
    user.hashed_password = "hashed_password_here"
    user.verified = True
    return user


@pytest.fixture
def mock_response():
    response = MagicMock()
    response.set_cookie = MagicMock()
    response.delete_cookie = MagicMock()
    return response


class TestAuthRouter:

    @pytest.mark.asyncio
    @patch("server.routers.auth.UserRepository")
    @patch("server.routers.auth.Auth")
    @patch("server.routers.auth.redis_client")
    async def test_register_success(self, mock_redis_client, mock_auth, mock_user_repo, mock_db, mock_user, mock_response):
        """Test successful user registration"""
        # Setup
        mock_user_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_user_repo_instance
        mock_user_repo_instance.get_by_email = AsyncMock(return_value=None)  # User doesn't exist yet
        mock_user_repo_instance.create_user = AsyncMock(return_value=mock_user)
        
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        mock_auth_instance.get_password_hash.return_value = "hashed_password"
        mock_auth_instance.create_access_token.return_value = "access_token"
        mock_auth_instance.create_refresh_token.return_value = "refresh_token"
        
        # Mock redis methods
        mock_redis_client.set = AsyncMock()
        
        # Test data
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            first_name="Test User"
        )
        
        # Execute - call the actual handler function, not the router endpoint
        result = await register(user_data, mock_response, mock_db)
        
        # Assert
        mock_user_repo_instance.get_by_email.assert_called_once_with(user_data.email)
        mock_user_repo_instance.create_user.assert_called_once()
        mock_auth_instance.create_access_token.assert_called_once()
        mock_auth_instance.create_refresh_token.assert_called_once()
        mock_response.set_cookie.assert_called()
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        # Check user field attributes instead of the whole object
        assert result.user.id == mock_user.id
        assert result.user.email == mock_user.email
        assert result.user.first_name == mock_user.first_name

    @pytest.mark.asyncio
    @patch("server.routers.auth.UserRepository")
    async def test_register_user_exists(self, mock_user_repo, mock_db, mock_user, mock_response):
        """Test registration when user already exists"""
        # Setup
        mock_user_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_user_repo_instance
        mock_user_repo_instance.get_by_email = AsyncMock(return_value=mock_user)  # User already exists
        
        # Test data
        user_data = UserCreate(
            email="test@example.com",
            password="password123",
            first_name="Test User"
        )
        
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await register(user_data, mock_response, mock_db)
        
        assert excinfo.value.status_code == 400
        assert "Пользователь с таким email уже существует" in excinfo.value.detail

    @pytest.mark.asyncio
    @patch("server.routers.auth.UserRepository")
    @patch("server.routers.auth.Auth")
    @patch("server.routers.auth.redis_client")
    async def test_login_success(self, mock_redis_client, mock_auth, mock_user_repo, mock_db, mock_user, mock_response):
        """Test successful login"""
        # Setup
        mock_user_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_user_repo_instance
        mock_user_repo_instance.get_by_email = AsyncMock(return_value=mock_user)
        
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        mock_auth_instance.verify_password.return_value = True
        mock_auth_instance.create_access_token.return_value = "access_token"
        mock_auth_instance.create_refresh_token.return_value = "refresh_token"
        
        # Mock redis methods
        mock_redis_client.set = AsyncMock()
        
        # Test data
        login_data = UserLogin(
            email="test@example.com",
            password="password123"
        )
        
        # Execute
        result = await login(login_data, mock_response, mock_db)
        
        # Assert
        mock_user_repo_instance.get_by_email.assert_called_once_with(login_data.email)
        mock_auth_instance.verify_password.assert_called_once()
        mock_auth_instance.create_access_token.assert_called_once()
        mock_auth_instance.create_refresh_token.assert_called_once()
        mock_response.set_cookie.assert_called()
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        # Check user field attributes instead of the whole object
        assert result.user.id == mock_user.id
        assert result.user.email == mock_user.email
        assert result.user.first_name == mock_user.first_name

    @pytest.mark.asyncio
    @patch("server.routers.auth.UserRepository")
    async def test_login_invalid_email(self, mock_user_repo, mock_db, mock_response):
        """Test login with invalid email"""
        # Setup
        mock_user_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_user_repo_instance
        mock_user_repo_instance.get_by_email = AsyncMock(return_value=None)  # User not found
        
        # Test data
        login_data = UserLogin(
            email="nonexistent@example.com",
            password="password123"
        )
        
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await login(login_data, mock_response, mock_db)
        
        assert excinfo.value.status_code == 400
        assert "Неверный email" in excinfo.value.detail

    @pytest.mark.asyncio
    @patch("server.routers.auth.UserRepository")
    @patch("server.routers.auth.Auth")
    async def test_login_invalid_password(self, mock_auth, mock_user_repo, mock_db, mock_user, mock_response):
        """Test login with invalid password"""
        # Setup
        mock_user_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_user_repo_instance
        mock_user_repo_instance.get_by_email = AsyncMock(return_value=mock_user)
        
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        mock_auth_instance.verify_password.return_value = False  # Password verification fails
        
        # Test data
        login_data = UserLogin(
            email="test@example.com",
            password="wrong_password"
        )
        
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await login(login_data, mock_response, mock_db)
        
        assert excinfo.value.status_code == 400
        assert "Неверный пароль" in excinfo.value.detail

    @pytest.mark.asyncio
    @patch("server.routers.auth.UserRepository")
    @patch("server.routers.auth.Auth")
    @patch("server.routers.auth.jwt.decode")
    @patch("server.routers.auth.redis_client")
    async def test_refresh_tokens_success(self, mock_redis_client, mock_jwt_decode, mock_auth, mock_user_repo, mock_db, mock_user, mock_response):
        """Test successful token refresh"""
        # Setup
        mock_user_id = str(mock_user.id)
        mock_jwt_decode.return_value = {"sub": mock_user_id}
        
        mock_user_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_user_repo_instance
        mock_user_repo_instance.get_by_id = AsyncMock(return_value=mock_user)
        
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        mock_auth_instance.create_access_token.return_value = "new_access_token"
        mock_auth_instance.create_refresh_token.return_value = "new_refresh_token"
        
        # Mock redis to validate refresh token
        mock_redis_client.get = AsyncMock(return_value=b"refresh_token")
        mock_redis_client.set = AsyncMock()
        
        # Execute
        result = await refresh_tokens("refresh_token", mock_response, mock_db)
        
        # Assert
        mock_jwt_decode.assert_called_once()
        mock_user_repo_instance.get_by_id.assert_called_once_with(uuid.UUID(mock_user_id))
        mock_redis_client.get.assert_called_once()
        mock_auth_instance.create_access_token.assert_called_once()
        mock_auth_instance.create_refresh_token.assert_called_once()
        mock_redis_client.set.assert_called()
        mock_response.set_cookie.assert_called()
        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"
        # Check user field attributes instead of the whole object
        assert result.user.id == mock_user.id
        assert result.user.email == mock_user.email
        assert result.user.first_name == mock_user.first_name

    @pytest.mark.asyncio
    @patch("server.routers.auth.jwt.decode")
    async def test_refresh_invalid_token(self, mock_jwt_decode, mock_db, mock_response):
        """Test refresh with invalid token"""
        # Setup
        mock_jwt_decode.side_effect = jwt.PyJWTError("Invalid token")
        
        # Execute and Assert
        with pytest.raises(HTTPException) as excinfo:
            await refresh_tokens("invalid_refresh_token", mock_response, mock_db)
        
        assert excinfo.value.status_code == 401
        assert "Неверный refresh token" in excinfo.value.detail

    @pytest.mark.asyncio
    @patch("server.routers.auth.redis_client")
    async def test_logout_success(self, mock_redis_client, mock_user, mock_response):
        """Test successful logout"""
        # Setup
        mock_redis_client.delete = AsyncMock()
        
        # Execute
        result = await logout(mock_response, mock_user)
        
        # Assert
        mock_redis_client.delete.assert_called()
        mock_response.delete_cookie.assert_called()
        assert result["detail"] == "Вы успешно вышли из аккаунта"
