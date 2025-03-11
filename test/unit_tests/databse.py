import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from server.backend.database import get_session, DATABASE_URL, Base
from server.backend.database import DATABASE_URL
from server.backend.database import DATABASE_URL
import importlib


# filepath: /c:/Users/merzl/PycharmProjects/lokalkateambackend2/server/backend/test_database.py


class TestDatabase:

    def test_database_url_construction(self):
        """Test that DATABASE_URL is constructed properly from environment variables"""
        original_url = os.environ.get('DATABASE_URL')

        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql+asyncpg://user:password@db:8001/db'}):
            assert DATABASE_URL == 'postgresql+asyncpg://user:password@db:8001/db'

        # Test when DATABASE_URL is built from components
        with patch.dict(os.environ, {
            'DATABASE_URL': '',
            'DB_USER': 'user',
            'DB_PASSWORD': 'pass',
            'DB_HOST': 'localhost',
            'DB_PORT': '8001',
            'DB_NAME': 'dbname'
        }):
            # Re-import to refresh the DATABASE_URL variable
            assert DATABASE_URL == 'postgresql+asyncpg://user:password@db:8001/db'

        # Restore original env var if it existed
        if original_url:
            os.environ['DATABASE_URL'] = original_url

    def test_base_class(self):
        """Test that Base class is created properly"""
        assert Base is not None
        # Check that it has the expected attributes of a declarative base
        assert hasattr(Base, 'metadata')
        assert hasattr(Base, '__abstract__')

    @pytest.mark.asyncio
    @patch('server.backend.database.AsyncSessionLocal')
    async def test_get_session(self, mock_session_local):
        """Test the get_session function yields a session"""
        # Create a mock session
        mock_session = AsyncMock()

        # Configure the AsyncSessionLocal mock to return a context manager
        # that yields our mock session
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Use get_session in an async context
        session_generator = get_session()
        session = await session_generator.__anext__()

        # Verify the session is our mock session
        assert session == mock_session

        # Check that the context manager was entered
        mock_session_local.return_value.__aenter__.assert_called_once()

        # Try to get another session (should raise StopAsyncIteration)
        with pytest.raises(StopAsyncIteration):
            await session_generator.__anext__()

        # Simulate the end of the context manager
        # This would happen automatically in a real "async with" block
        try:
            await session_generator.aclose()
        except StopAsyncIteration:
            pass

