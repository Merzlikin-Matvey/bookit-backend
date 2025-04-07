import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from server.repositories.user import UserRepository
from server.models.user import User
from server.schemas.user import UserCreate

@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    execute_result = MagicMock()
    scalars_result = MagicMock()
    scalars_result.first = MagicMock()
    scalars_result.all = MagicMock()
    execute_result.scalars.return_value = scalars_result
    db.execute.return_value = execute_result
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = AsyncMock()
    return db

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.login = "test@example.com"
    user.first_name = "Test User"
    user.hashed_password = "hashedpassword123"
    user.role = "user"
    user.yandex_id = None
    user.telegram_id = None
    return user

class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_by_email(self, mock_db, mock_user):
        repo = UserRepository(mock_db)
        email = "test@example.com"
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = result_mock
        result = await repo.get_by_email(email)
        mock_db.execute.assert_called_once()
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_db, mock_user):
        repo = UserRepository(mock_db)
        user_id = mock_user.id
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = result_mock
        result = await repo.get_by_id(user_id)
        mock_db.execute.assert_called_once()
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_by_yandex_id(self, mock_db, mock_user):
        repo = UserRepository(mock_db)
        yandex_id = "yandex123"
        mock_user.yandex_id = yandex_id
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = result_mock
        result = await repo.get_by_yandex_id(yandex_id)
        mock_db.execute.assert_called_once()
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_create_user(self, mock_db):
        repo = UserRepository(mock_db)
        user_data = UserCreate(email="new@example.com", first_name="New User", password="password123", role="user")
        hashed_password = "hashedpassword123"
        result = await repo.create_user(user_data, hashed_password)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        created_user = mock_db.add.call_args[0][0]
        assert created_user.email == user_data.email
        assert created_user.login == user_data.email
        assert created_user.first_name == user_data.first_name
        assert created_user.hashed_password == hashed_password
        assert created_user.role == user_data.role
        assert result == created_user

    @pytest.mark.asyncio
    async def test_create_user_yandex(self, mock_db):
        repo = UserRepository(mock_db)
        yandex_data = {"id": "yandex123", "default_email": "yandex@example.com", "first_name": "Yandex User"}
        result = await repo.create_user_yandex(yandex_data)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        created_user = mock_db.add.call_args[0][0]
        assert created_user.yandex_id == yandex_data["id"]
        assert created_user.email == yandex_data["default_email"]
        assert created_user.login == yandex_data["default_email"]
        assert created_user.first_name == yandex_data["first_name"]
        assert created_user.hashed_password == ""
        assert result == created_user

    @pytest.mark.asyncio
    async def test_create_user_yandex_alternate_email_field(self, mock_db):
        repo = UserRepository(mock_db)
        yandex_data = {"id": "yandex123", "email": "yandex@example.com", "first_name": "Yandex User"}
        result = await repo.create_user_yandex(yandex_data)
        created_user = mock_db.add.call_args[0][0]
        assert created_user.email == yandex_data["email"]

    @pytest.mark.asyncio
    async def test_update_user(self, mock_db, mock_user):
        repo = UserRepository(mock_db)
        user_id = mock_user.id
        update_data = {"first_name": "Updated Name", "role": "admin"}
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_user
        mock_db.execute.return_value = result_mock
        result = await repo.update_user(user_id, update_data)
        assert mock_user.first_name == update_data["first_name"]
        assert mock_user.role == update_data["role"]
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, mock_db):
        repo = UserRepository(mock_db)
        user_id = uuid4()
        update_data = {"first_name": "Updated Name"}
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return.value = None
        mock_db.execute.return_value = result_mock
        result = await repo.update_user(user_id, update_data)
        assert result is None
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_user(self, mock_db, mock_user):
        repo = UserRepository(mock_db)
        user_id = mock_user.id
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return.value = mock_user
        mock_db.execute.return_value = result_mock
        result = await repo.delete_user(user_id)
        mock_db.execute.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, mock_db):
        repo = UserRepository(mock_db)
        user_id = uuid4()
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return.value = None
        mock_db.execute.return_value = result_mock
        result = await repo.delete_user(user_id)
        mock_db.execute.assert_called_once()
        mock_db.delete.assert_not_called()
        mock_db.commit.assert.not_called()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_user_by_telegram(self, mock_db, mock_user):
        repo = UserRepository(mock_db)
        telegram_id = "123456789"
        mock_user.telegram_id = telegram_id
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return.value = mock_user
        mock_db.execute.return_value = result_mock
        result = await repo.get_user_by_telegram(telegram_id)
        mock_db.execute.assert_called_once()
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_get_all_admins(self, mock_db, mock_user):
        repo = UserRepository(mock_db)
        mock_user.role = "admin"
        admin_users = [mock_user, MagicMock(), MagicMock()]
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return.value = admin_users
        mock_db.execute.return.value = result_mock
        result = await repo.get_all_admins()
        mock_db.execute.assert_called_once()
        assert result == admin_users
