import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from server.repositories.reservation import ReservationRepository
from server.schemas.reservation import ReservationCreate, ReservationUpdate
from server.schemas.reservation import ReservationStatusEnum
from server.utils.exceptions import SeatIsNotAvailableError
from server.utils.datetime_utils import MOSCOW_TZ

@pytest.fixture
def mock_db():
    db = AsyncMock()
    execute_result = MagicMock()
    scalars_result = MagicMock()
    scalars_result.first = MagicMock()
    scalars_result.all = MagicMock()
    execute_result.scalars.return_value = scalars_result
    db.execute.return_value = execute_result
    return db

@pytest.fixture
def mock_reservation():
    reservation = MagicMock()
    reservation.id = uuid4()
    reservation.user_id = uuid4()
    reservation.seat_id = uuid4()
    reservation.start = datetime.datetime(2023, 1, 1, 10, 0)
    reservation.end = datetime.datetime(2023, 1, 1, 12, 0)
    reservation.status = "future"
    return reservation

@pytest.fixture
def mock_seat():
    seat = MagicMock()
    seat.id = uuid4()
    seat.name = "Test Seat"
    return seat

class TestReservationRepository:
    @pytest.mark.asyncio
    @patch("server.repositories.reservation.SeatsManager")
    @patch("server.repositories.reservation.Reservation")
    @patch("server.repositories.reservation.make_timezone_naive")
    async def test_create_reservation_success(self, mock_make_naive, MockReservation, MockSeatsManager, mock_db):
        repo = ReservationRepository(mock_db)
        mock_manager = MockSeatsManager.return_value
        mock_manager.is_available = AsyncMock(return_value=True)
        start_time = datetime.datetime.now(tz=MOSCOW_TZ)
        end_time = start_time + datetime.timedelta(hours=2)
        mock_make_naive.side_effect = lambda dt: dt.replace(tzinfo=None)
        user_id = uuid4()
        seat_id = uuid4()
        mock_reservation = MockReservation.return_value
        reservation_data = ReservationCreate(user_id=user_id, seat_id=seat_id, start=start_time, end=end_time)
        result = await repo.create_reservation(reservation_data)
        MockSeatsManager.assert_called_once_with(mock_db)
        mock_manager.is_available.assert_called_once_with(seat_id, start_time, end_time)
        MockReservation.assert_called_once()
        mock_db.add.assert_called_once_with(mock_reservation)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_reservation)
        assert result == mock_reservation

    @pytest.mark.asyncio
    @patch("server.repositories.reservation.SeatsManager")
    @patch("server.repositories.reservation.Reservation")
    @patch("server.repositories.reservation.make_timezone_naive")
    async def test_create_reservation_failure(self, mock_make_naive, MockReservation, MockSeatsManager, mock_db):
        repo = ReservationRepository(mock_db)
        mock_manager = MockSeatsManager.return_value
        mock_manager.is_available = AsyncMock(return_value=False)
        start_time = datetime.datetime.now(tz=MOSCOW_TZ)
        end_time = start_time + datetime.timedelta(hours=2)
        mock_make_naive.side_effect = lambda dt: dt.replace(tzinfo=None)
        user_id = uuid4()
        seat_id = uuid4()
        reservation_data = ReservationCreate(user_id=user_id, seat_id=seat_id, start=start_time, end=end_time)
        with pytest.raises(SeatIsNotAvailableError):
            await repo.create_reservation(reservation_data)
        MockSeatsManager.assert_called_once_with(mock_db)
        mock_manager.is_available.assert_called_once_with(seat_id, start_time, end_time)
        MockReservation.assert_not_called()
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    @patch("server.repositories.reservation.select")
    @patch("server.repositories.reservation.Reservation")
    async def test_get_reservation_by_id(self, MockReservation, mock_select, mock_db, mock_reservation):
        repo = ReservationRepository(mock_db)
        reservation_id = uuid4()
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_reservation
        result = await repo.get_by_id(reservation_id)
        mock_select.assert_called_once()
        mock_db.execute.assert_called_once()
        assert result == mock_reservation

    @pytest.mark.asyncio
    @patch("server.repositories.reservation.select")
    @patch("server.repositories.reservation.Reservation")
    async def test_get_reservation_not_found(self, MockReservation, mock_select, mock_db):
        repo = ReservationRepository(mock_db)
        reservation_id = uuid4()
        mock_db.execute.return_value.scalars.return_value.first.return_value = None
        result = await repo.get_by_id(reservation_id)
        mock_select.assert_called_once()
        mock_db.execute.assert_called_once()
        assert result is None

    @pytest.mark.asyncio
    @patch("server.repositories.reservation.select")
    @patch("server.repositories.reservation.Reservation")
    async def test_get_reservations(self, MockReservation, mock_select, mock_db, mock_reservation):
        repo = ReservationRepository(mock_db)
        mock_reservations = [mock_reservation, MagicMock(), MagicMock()]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_reservations
        result = await repo.get_all_reservations()
        mock_select.assert_called_once()
        mock_db.execute.assert_called_once()
        assert result == mock_reservations

    @pytest.mark.asyncio
    @patch("server.repositories.reservation.select")
    @patch("server.repositories.reservation.Reservation")
    @patch("server.repositories.reservation.Seat")
    async def test_get_user_reservations(self, MockSeat, MockReservation, mock_select, mock_db, mock_reservation):
        repo = ReservationRepository(mock_db)
        user_id = uuid4()
        mock_reservations = [mock_reservation, MagicMock()]
        mock_seat = MagicMock()
        mock_seat.name = "Test Seat"
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_reservations
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_seat
        result = await repo.get_reservations_by_user_id(user_id)
        mock_select.assert_called()
        assert len(result) == len(mock_reservations)

    @pytest.mark.asyncio
    @patch("server.repositories.reservation.SeatsManager")
    @patch("server.repositories.reservation.select")
    @patch("server.repositories.reservation.make_timezone_naive")
    async def test_update_reservation(self, mock_make_naive, mock_select, MockSeatsManager, mock_db, mock_reservation):
        repo = ReservationRepository(mock_db)
        reservation_id = uuid4()
        mock_manager = MockSeatsManager.return_value
        mock_manager.is_available = AsyncMock(return_value=True)
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_reservation
        start_time = datetime.datetime.now(tz=MOSCOW_TZ)
        end_time = start_time + datetime.timedelta(hours=3)
        mock_make_naive.side_effect = lambda dt: dt.replace(tzinfo=None)
        update_data = ReservationUpdate(start=start_time, end=end_time, status=ReservationStatusEnum.ACTIVE)
        result = await repo.update_reservation(reservation_id, update_data)
        assert result == mock_reservation

    @pytest.mark.asyncio
    @patch("server.repositories.reservation.select")
    @patch("server.repositories.reservation.Reservation")
    async def test_delete_reservation(self, MockReservation, mock_select, mock_db, mock_reservation):
        repo = ReservationRepository(mock_db)
        reservation_id = uuid4()
        mock_db.execute.return_value.scalars.return_value.first.return_value = mock_reservation
        result = await repo.delete_reservation(reservation_id)
        mock_select.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_reservation)
        mock_db.commit.assert_called_once()
        assert result is True