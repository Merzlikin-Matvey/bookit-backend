import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from server.services.seats_manager import SeatsManager
from server.models.reservation import Reservation


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
    reservation.seat_id = uuid4()
    reservation.start = datetime(2023, 1, 1, 10, 0)
    reservation.end = datetime(2023, 1, 1, 12, 0)
    return reservation


class TestSeatsManager:

    @pytest.mark.asyncio
    async def test_is_available_no_reservations(self, mock_db):
        """Test seat is available when there are no reservations"""
        manager = SeatsManager(mock_db)
        seat_id = uuid4()
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 14, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 16, 0, tzinfo=timezone.utc)
        
        result = await manager.is_available(seat_id, start, end)
        
        mock_db.execute.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_with_non_overlapping_reservation(self, mock_db, mock_reservation):
        """Test seat is available when reservation doesn't overlap"""
        manager = SeatsManager(mock_db)
        seat_id = mock_reservation.seat_id
        
        mock_reservation.start = datetime(2023, 1, 1, 10, 0)
        mock_reservation.end = datetime(2023, 1, 1, 12, 0)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [mock_reservation]
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 14, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 16, 0, tzinfo=timezone.utc)
        
        result = await manager.is_available(seat_id, start, end)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_with_overlapping_reservation(self, mock_db, mock_reservation):
        """Test seat is unavailable when reservation overlaps"""
        manager = SeatsManager(mock_db)
        seat_id = mock_reservation.seat_id
        
        mock_reservation.start = datetime(2023, 1, 1, 10, 0)
        mock_reservation.end = datetime(2023, 1, 1, 12, 0)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [mock_reservation]
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 13, 0, tzinfo=timezone.utc)
        
        result = await manager.is_available(seat_id, start, end)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_is_available_edge_case_touching_start(self, mock_db, mock_reservation):
        """Test seat is available when new reservation starts exactly when existing one ends"""
        manager = SeatsManager(mock_db)
        seat_id = mock_reservation.seat_id
        
        mock_reservation.start = datetime(2023, 1, 1, 10, 0)
        mock_reservation.end = datetime(2023, 1, 1, 12, 0)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [mock_reservation]
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 14, 0, tzinfo=timezone.utc)
        
        result = await manager.is_available(seat_id, start, end)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_edge_case_touching_end(self, mock_db, mock_reservation):
        """Test seat is available when new reservation ends exactly when existing one starts"""
        manager = SeatsManager(mock_db)
        seat_id = mock_reservation.seat_id
        
        mock_reservation.start = datetime(2023, 1, 1, 12, 0)
        mock_reservation.end = datetime(2023, 1, 1, 14, 0)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [mock_reservation]
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
        
        result = await manager.is_available(seat_id, start, end)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_get_occupied_seats_none_occupied(self, mock_db):
        """Test getting occupied seats when none are occupied"""
        manager = SeatsManager(mock_db)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 14, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 16, 0, tzinfo=timezone.utc)
        
        result = await manager.get_occupied_seats(start, end)
        
        mock_db.execute.assert_called_once()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_occupied_seats_some_occupied(self, mock_db):
        """Test getting occupied seats when some are occupied"""
        manager = SeatsManager(mock_db)
        
        seat_id1 = str(uuid4())
        seat_id2 = str(uuid4())
        
        reservation1 = MagicMock()
        reservation1.seat_id = seat_id1
        reservation1.start = datetime(2023, 1, 1, 10, 0)
        reservation1.end = datetime(2023, 1, 1, 12, 0)
        
        reservation2 = MagicMock()
        reservation2.seat_id = seat_id2
        reservation2.start = datetime(2023, 1, 1, 11, 0)
        reservation2.end = datetime(2023, 1, 1, 13, 0)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [reservation1, reservation2]
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 11, 30, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 30, tzinfo=timezone.utc)
        
        result = await manager.get_occupied_seats(start, end)
        
        mock_db.execute.assert_called_once()
        assert sorted(result) == sorted([seat_id1, seat_id2])

    @pytest.mark.asyncio
    async def test_get_occupied_seats_multiple_reservations_same_seat(self, mock_db):
        """Test getting occupied seats with multiple reservations for the same seat"""
        manager = SeatsManager(mock_db)
        seat_id = str(uuid4())
        
        reservation1 = MagicMock()
        reservation1.seat_id = seat_id
        reservation1.start = datetime(2023, 1, 1, 10, 0)
        reservation1.end = datetime(2023, 1, 1, 12, 0)
        
        reservation2 = MagicMock()
        reservation2.seat_id = seat_id
        reservation2.start = datetime(2023, 1, 1, 14, 0)
        reservation2.end = datetime(2023, 1, 1, 16, 0)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [reservation1, reservation2]
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 30, tzinfo=timezone.utc)
        
        result = await manager.get_occupied_seats(start, end)
        
        assert result == [seat_id]
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_timezone_handling(self, mock_db, mock_reservation):
        """Test handling of timezone-aware and naive datetime objects"""
        manager = SeatsManager(mock_db)
        seat_id = mock_reservation.seat_id
        
        mock_reservation.start = datetime(2023, 1, 1, 10, 0)
        mock_reservation.end = datetime(2023, 1, 1, 12, 0)
        
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [mock_reservation]
        mock_db.execute.return_value = result_mock
        
        start = datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 13, 0, tzinfo=timezone.utc)
        
        result = await manager.is_available(seat_id, start, end)
        
        assert result is False
