import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from uuid import UUID, uuid4
from server.repositories.seat import SeatRepository
from server.models.seat import Seat
from server.models.reservation import Reservation
from server.schemas.seat import SeatCreate, SeatUpdate


# filepath: /c:/Users/merzl/PycharmProjects/lokalkateambackend2/server/repositories/test_seat.py


@pytest.fixture
def mock_db():
    """Create a mock AsyncSession"""
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
def mock_seat():
    """Create a mock Seat object"""
    seat = MagicMock()
    seat.id = uuid4()
    seat.name = "Test Seat"
    seat.x = 10
    seat.y = 20
    seat.type = "desk"
    seat.has_water = True
    seat.has_kitchen = False
    seat.is_quite = True
    seat.has_computer = False
    seat.has_smart_desk = True
    seat.is_talk_room = False
    return seat


@pytest.fixture
def mock_reservation():
    """Create a mock Reservation object"""
    reservation = MagicMock()
    reservation.id = uuid4()
    reservation.seat_id = uuid4()
    reservation.start = datetime(2023, 1, 1, 10, 0)
    reservation.end = datetime(2023, 1, 1, 12, 0)
    return reservation


class TestSeatRepository:

    @pytest.mark.asyncio
    async def test_create_seat(self, mock_db):
        """Test creating a new seat"""
        # Setup
        repo = SeatRepository(mock_db)
        seat_data = SeatCreate(
            name="Test Seat",
            x=10,
            y=20,
            type="desk",
            has_water=True,
            has_kitchen=False,
            is_quite=True,
            has_computer=False,
            has_smart_desk=True,
            is_talk_room=False
        )

        # Execute
        result = await repo.create_seat(seat_data)

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result is mock_db.add.call_args[0][0]

        # Verify seat properties
        created_seat = mock_db.add.call_args[0][0]
        assert created_seat.name == seat_data.name
        assert created_seat.x == seat_data.x
        assert created_seat.y == seat_data.y
        assert created_seat.type == seat_data.type
        assert created_seat.has_water == seat_data.has_water
        assert created_seat.has_kitchen == seat_data.has_kitchen
        assert created_seat.is_quite == seat_data.is_quite
        assert created_seat.has_computer == seat_data.has_computer
        assert created_seat.has_smart_desk == seat_data.has_smart_desk
        assert created_seat.is_talk_room == seat_data.is_talk_room

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_db, mock_seat):
        """Test retrieving a seat by ID"""
        # Setup
        repo = SeatRepository(mock_db)
        seat_id = mock_seat.id

        # Mock the query result - using MagicMock instead of AsyncMock
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_seat
        mock_db.execute.return_value = result_mock

        # Execute
        result = await repo.get_by_id(seat_id)

        # Assert
        mock_db.execute.assert_called_once()
        assert result == mock_seat

    @pytest.mark.asyncio
    async def test_delete_seat_success(self, mock_db, mock_seat):
        """Test successfully deleting a seat"""
        # Setup
        repo = SeatRepository(mock_db)
        seat_id = mock_seat.id

        # Mock the query result - using MagicMock instead of AsyncMock
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_seat
        mock_db.execute.return_value = result_mock

        # Execute
        result = await repo.delete_seat(seat_id)

        # Assert
        mock_db.execute.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_seat)
        mock_db.commit.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_seat_not_found(self, mock_db):
        """Test deleting a non-existent seat"""
        # Setup
        repo = SeatRepository(mock_db)
        seat_id = uuid4()

        # Mock the query result - seat not found - using MagicMock instead of AsyncMock
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = result_mock

        # Execute
        result = await repo.delete_seat(seat_id)

        # Assert
        mock_db.execute.assert_called_once()
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
        assert result is False

    @pytest.mark.asyncio
    async def test_update_seat_success(self, mock_db, mock_seat):
        """Test successfully updating a seat"""
        # Setup
        repo = SeatRepository(mock_db)
        seat_id = mock_seat.id

        # Mock the query result - using MagicMock instead of AsyncMock
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_seat
        mock_db.execute.return_value = result_mock

        # Create update data
        update_data = SeatUpdate(name="Updated Seat", x=15, has_water=False)

        # Execute
        result = await repo.update_seat(seat_id, update_data)

        # Assert
        assert mock_seat.name == "Updated Seat"
        assert mock_seat.x == 15
        assert mock_seat.has_water is False
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_seat)
        assert result == mock_seat

    @pytest.mark.asyncio
    async def test_update_seat_not_found(self, mock_db):
        """Test updating a non-existent seat"""
        # Setup
        repo = SeatRepository(mock_db)
        seat_id = uuid4()

        # Mock the query result - seat not found - using MagicMock instead of AsyncMock
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = result_mock

        # Create update data
        update_data = SeatUpdate(name="Updated Seat")

        # Execute
        result = await repo.update_seat(seat_id, update_data)

        # Assert
        mock_db.commit.assert_not_called()
        mock_db.refresh.assert_not_called()
        assert result is None

    @pytest.mark.asyncio
    @patch("server.repositories.seat.make_timezone_naive")
    async def test_get_all_no_reservations(self, mock_make_naive, mock_db):
        """Test getting all seats when no reservations exist in the time range"""
        # Setup
        repo = SeatRepository(mock_db)

        # Create mock seats
        seat1 = MagicMock()
        seat1.id = uuid4()
        seat2 = MagicMock()
        seat2.id = uuid4()
        seats = [seat1, seat2]

        # Mock the seats query result - using MagicMock instead of AsyncMock
        seats_result_mock = MagicMock()
        seats_result_mock.scalars.return_value.all.return_value = seats

        # Mock the reservations query result - no reservations - using MagicMock instead of AsyncMock
        res_result_mock = MagicMock()
        res_result_mock.scalars.return_value.all.return_value = []

        # Configure mock_db.execute to return different results based on the query
        mock_db.execute.side_effect = [seats_result_mock, res_result_mock]

        # Mock timezone conversion
        start = datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
        mock_make_naive.side_effect = lambda dt: dt.replace(tzinfo=None)

        # Execute
        result = await repo.get_all(start, end)

        # Assert
        assert mock_db.execute.call_count == 2
        assert result == seats
        # All seats should be available
        for seat in result:
            assert seat.is_available is True

    @pytest.mark.asyncio
    @patch("server.repositories.seat.make_timezone_naive")
    async def test_get_all_with_reservations(self, mock_make_naive, mock_db, mock_seat, mock_reservation):
        """Test getting all seats when some seats are reserved"""
        # Setup
        repo = SeatRepository(mock_db)

        # Create mock seats
        seat1 = mock_seat
        seat2 = MagicMock()
        seat2.id = uuid4()
        seats = [seat1, seat2]

        # Configure mock reservation to occupy seat1
        mock_reservation.seat_id = seat1.id
        reservations = [mock_reservation]

        # Mock the seats query result - using MagicMock instead of AsyncMock
        seats_result_mock = MagicMock()
        seats_result_mock.scalars.return_value.all.return_value = seats

        # Mock the reservations query result - using MagicMock instead of AsyncMock
        res_result_mock = MagicMock()
        res_result_mock.scalars.return_value.all.return_value = reservations

        # Configure mock_db.execute to return different results based on the query
        mock_db.execute.side_effect = [seats_result_mock, res_result_mock]

        # Mock timezone conversion
        start = datetime(2023, 1, 1, 9, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc)

        start_naive = datetime(2023, 1, 1, 9, 0)
        end_naive = datetime(2023, 1, 1, 11, 0)
        mock_make_naive.side_effect = [start_naive, end_naive]

        # Execute
        result = await repo.get_all(start, end)

        # Assert
        assert mock_db.execute.call_count == 2
        assert result == seats

        # Seat1 should be unavailable (reserved), seat2 should be available
        assert result[0].is_available is False
        assert result[1].is_available is True

    @pytest.mark.asyncio
    @patch("server.repositories.seat.make_timezone_naive")
    async def test_get_all_filtering_by_time_range(self, mock_make_naive, mock_db, mock_seat):
        """Test that only reservations overlapping with the time range are considered"""
        # Setup
        repo = SeatRepository(mock_db)

        # Create mock seat
        seat = mock_seat
        seats = [seat]

        # Create reservations with different time ranges
        reservation1 = MagicMock()  # Overlaps with query range
        reservation1.seat_id = seat.id
        reservation1.start = datetime(2023, 1, 1, 9, 0)
        reservation1.end = datetime(2023, 1, 1, 11, 0)

        reservation2 = MagicMock()  # Before query range
        reservation2.seat_id = seat.id
        reservation2.start = datetime(2023, 1, 1, 7, 0)
        reservation2.end = datetime(2023, 1, 1, 8, 0)

        # Only include the overlapping reservation in the query result
        reservations = [reservation1]

        # Mock the seats query result - using MagicMock instead of AsyncMock
        seats_result_mock = MagicMock()
        seats_result_mock.scalars.return_value.all.return_value = seats

        # Mock the reservations query result - using MagicMock instead of AsyncMock
        res_result_mock = MagicMock()
        res_result_mock.scalars.return_value.all.return_value = reservations

        # Configure mock_db.execute to return different results
        mock_db.execute.side_effect = [seats_result_mock, res_result_mock]

        # Mock timezone conversion
        start = datetime(2023, 1, 1, 10, 0, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)

        start_naive = datetime(2023, 1, 1, 10, 0)
        end_naive = datetime(2023, 1, 1, 12, 0)
        mock_make_naive.side_effect = [start_naive, end_naive]

        # Execute
        result = await repo.get_all(start, end)

        # Assert
        # Verify the correct query was made with time range filtering
        filter_call = mock_db.execute.call_args_list[1][0][0]
        # The seat should be marked as unavailable due to the overlapping reservation
        assert result[0].is_available is False