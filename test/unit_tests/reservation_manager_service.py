import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from server.services.reservation import ReservationManager
from server.models.reservation import Reservation
from server.models.seat import Seat
from server.utils.exceptions import UserAlreadyHasActiveReservationError


@pytest.fixture
def mock_db():
    """Create a mock AsyncSession"""
    db = AsyncMock()
    return db


@pytest.fixture
def mock_reservation():
    """Create a mock Reservation object"""
    reservation = MagicMock()
    reservation.id = uuid4()
    reservation.user_id = str(uuid4())
    reservation.seat_id = str(uuid4())
    reservation.start = datetime(2023, 1, 1, 10, 0)
    reservation.end = datetime(2023, 1, 1, 12, 0)
    reservation.status = "active"
    return reservation


@pytest.fixture
def mock_seat():
    """Create a mock Seat object"""
    seat = MagicMock()
    seat.id = uuid4()
    seat.name = "Test Seat"
    return seat


class TestReservationManager:

    @pytest.mark.asyncio
    @patch("server.services.reservation.datetime")
    async def test_does_user_have_active_reservation_no_reservation(self, mock_datetime, mock_db):
        """Test when user has no active reservations"""
        # Setup
        manager = ReservationManager(mock_db)
        user_id = str(uuid4())
        
        # Mock current time
        now = datetime(2023, 1, 1, 12, 0)
        mock_datetime.utcnow.return_value = now
        
        # Mock query result - no reservations
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = result_mock
        
        # Execute
        result = await manager.does_user_have_active_reservation(user_id)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is False

    @pytest.mark.asyncio
    @patch("server.services.reservation.datetime")
    async def test_does_user_have_active_reservation_has_reservation(self, mock_datetime, mock_db, mock_reservation):
        """Test when user has an active reservation"""
        # Setup
        manager = ReservationManager(mock_db)
        user_id = mock_reservation.user_id
        
        # Mock current time
        now = datetime(2023, 1, 1, 11, 0)  # During the reservation
        mock_datetime.utcnow.return_value = now
        
        # Mock query result - has active reservation
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_reservation
        mock_db.execute.return_value = result_mock
        
        # Execute
        result = await manager.does_user_have_active_reservation(user_id)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    @patch("server.services.reservation.datetime")
    async def test_does_user_have_active_reservation_closed_only(self, mock_datetime, mock_db, mock_reservation):
        """Test when user only has closed reservations"""
        # Setup
        manager = ReservationManager(mock_db)
        user_id = mock_reservation.user_id
        
        # Set reservation as closed
        mock_reservation.status = "closed"
        
        # Mock current time
        now = datetime(2023, 1, 1, 11, 0)  # During the reservation
        mock_datetime.utcnow.return_value = now
        
        # Mock query result - no active reservations (first() returns None)
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = result_mock
        
        # Execute
        result = await manager.does_user_have_active_reservation(user_id)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is False

    @pytest.mark.asyncio
    async def test_create_reservation_success(self, mock_db):
        """Test successful reservation creation"""
        # Setup
        manager = ReservationManager(mock_db)
        
        # Mock does_user_have_active_reservation to return False
        manager.does_user_have_active_reservation = AsyncMock(return_value=False)
        
        # Define reservation parameters
        user_id = str(uuid4())
        seat_id = str(uuid4())
        start = datetime(2023, 1, 1, 14, 0)
        end = datetime(2023, 1, 1, 16, 0)
        
        # Execute
        result = await manager.create_reservation(user_id, start, end, seat_id)
        
        # Assert
        manager.does_user_have_active_reservation.assert_called_once_with(user_id)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify the created reservation properties
        created_reservation = mock_db.add.call_args[0][0]
        assert created_reservation.user_id == user_id
        assert created_reservation.seat_id == seat_id
        assert created_reservation.start == start
        assert created_reservation.end == end

    @pytest.mark.asyncio
    async def test_create_reservation_already_has_active(self, mock_db):
        """Test reservation creation fails when user already has active reservation"""
        # Setup
        manager = ReservationManager(mock_db)
        
        # Mock does_user_have_active_reservation to return True
        manager.does_user_have_active_reservation = AsyncMock(return_value=True)
        
        # Define reservation parameters
        user_id = str(uuid4())
        seat_id = str(uuid4())
        start = datetime(2023, 1, 1, 14, 0)
        end = datetime(2023, 1, 1, 16, 0)
        
        # Execute and Assert
        with pytest.raises(UserAlreadyHasActiveReservationError) as excinfo:
            await manager.create_reservation(user_id, start, end, seat_id)
        
        # Verify the error has the correct user ID
        assert excinfo.value.user_id == user_id
        
        # Verify no DB operations were performed
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()

    @pytest.mark.asyncio
    @patch("server.services.reservation.datetime")
    async def test_get_active_user_reservation_has_active(self, mock_datetime, mock_db, mock_reservation, mock_seat):
        """Test getting active reservation when user has one"""
        # Setup
        manager = ReservationManager(mock_db)
        user_id = mock_reservation.user_id
        mock_reservation.seat_id = mock_seat.id
        
        # Mock current time
        now = datetime(2023, 1, 1, 11, 0)  # During the reservation
        mock_datetime.utcnow.return_value = now
        
        # Mock reservation query result
        res_result_mock = MagicMock()
        res_result_mock.scalars.return_value.first.return_value = mock_reservation
        
        # Mock seat query result
        seat_result_mock = MagicMock()
        seat_result_mock.scalars.return_value.first.return_value = mock_seat
        
        # Configure mock_db to return different results for different queries
        mock_db.execute.side_effect = [res_result_mock, seat_result_mock]
        
        # Execute
        result = await manager.get_active_user_reservation(user_id)
        
        # Assert
        assert mock_db.execute.call_count == 2
        assert result == mock_reservation
        assert result.seat_name == mock_seat.name

    @pytest.mark.asyncio
    @patch("server.services.reservation.datetime")
    async def test_get_active_user_reservation_no_active(self, mock_datetime, mock_db):
        """Test getting active reservation when user has none"""
        # Setup
        manager = ReservationManager(mock_db)
        user_id = str(uuid4())
        
        # Mock current time
        now = datetime(2023, 1, 1, 11, 0)
        mock_datetime.utcnow.return_value = now
        
        # Mock query result - no reservations
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = result_mock
        
        # Execute
        result = await manager.get_active_user_reservation(user_id)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_maximum_available_time_has_future_reservations(self, mock_db):
        """Test getting maximum available time when future reservations exist"""
        # Setup
        manager = ReservationManager(mock_db)
        user_id = str(uuid4())
        start_time = datetime(2023, 1, 1, 10, 0)
        
        # Set up the expected next reservation start time
        next_start = datetime(2023, 1, 1, 14, 0)
        
        # Mock query result
        result_mock = MagicMock()
        result_mock.scalar.return_value = next_start
        mock_db.execute.return_value = result_mock
        
        # Execute
        result = await manager.get_maximum_available_time(user_id, start_time)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result == next_start

    @pytest.mark.asyncio
    async def test_get_maximum_available_time_no_future_reservations(self, mock_db):
        """Test getting maximum available time when no future reservations exist"""
        # Setup
        manager = ReservationManager(mock_db)
        user_id = str(uuid4())
        start_time = datetime(2023, 1, 1, 10, 0)
        
        # Mock query result - no future reservations
        result_mock = MagicMock()
        result_mock.scalar.return_value = None
        mock_db.execute.return_value = result_mock
        
        # Execute
        result = await manager.get_maximum_available_time(user_id, start_time)
        
        # Assert
        mock_db.execute.assert_called_once()
        assert result == -58  # Special value indicating no limit
