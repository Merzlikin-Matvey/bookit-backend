import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, Response, status
from fastapi.testclient import TestClient
from sqlalchemy import select
from uuid import uuid4, UUID
from datetime import datetime, timezone

from server.routers.admin_panel import router, get_current_user_from_cookie
from server.models.user import User
from server.models.seat import Seat
from server.models.reservation import Reservation
from server.schemas.reservation import ReservationCreate, ReservationUpdate
from server.schemas.ticket import TicketStatusUpdate
from server.schemas.user import UserUpdateAdmin, UserOut
from server.utils.exceptions import SeatIsNotAvailableError, UserAlreadyHasActiveReservationError



@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = AsyncMock()
    return db


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user"""
    user = MagicMock()
    user.id = uuid4()
    user.email = "admin@example.com"
    user.role = "admin"
    user.verified = True
    return user


@pytest.fixture
def mock_regular_user():
    """Create a mock regular user"""
    user = MagicMock()
    user.id = uuid4()
    user.email = "user@example.com"
    user.role = "user"
    user.verified = False
    return user


@pytest.fixture
def mock_reservation():
    """Create a mock reservation"""
    reservation = MagicMock()
    reservation.id = uuid4()
    reservation.user_id = uuid4()
    reservation.seat_id = uuid4()
    reservation.start = datetime.now(timezone.utc)
    reservation.end = datetime.now(timezone.utc)
    reservation.status = "future"
    return reservation


@pytest.fixture
def mock_seat():
    """Create a mock seat"""
    seat = MagicMock()
    seat.id = uuid4()
    seat.name = "Test Seat"
    return seat


@pytest.fixture
def mock_ticket():
    """Create a mock ticket"""
    ticket = MagicMock()
    ticket.id = uuid4()
    ticket.user_id = uuid4()
    ticket.reservation_id = uuid4()
    ticket.seat_id = uuid4()
    ticket.theme = "Test Ticket"
    ticket.message = "This is a test ticket"
    ticket.status = None
    ticket.made_on = datetime.now()
    return ticket


@pytest.fixture(autouse=True)
def app():
    """Setup FastAPI test client with mocked dependencies"""
    app = MagicMock()
    app.dependency_overrides = {}
    return app


class TestAdminPanel:

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    async def test_check_qr_success(self, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_reservation):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        first_result = MagicMock()
        first_result.scalars.return_value.first.side_effect = [mock_reservation, mock_admin_user]
        mock_db.execute.return_value = first_result

        reservation_id = mock_reservation.id
        result = await router.routes[0].endpoint(reservation_id, mock_admin_user, mock_db)

        assert mock_reservation.status == "success"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    async def test_check_qr_not_admin(self, mock_get_current_user, mock_get_session, mock_db, mock_regular_user):
        mock_get_current_user.return_value = mock_regular_user
        mock_get_session.return_value = mock_db

        reservation_id = uuid4()
        with pytest.raises(HTTPException) as exc:
            await router.routes[0].endpoint(reservation_id, mock_regular_user, mock_db)
        
        assert exc.value.status_code == 403
        assert "Доступ запрещен" in exc.value.detail

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    async def test_check_qr_reservation_not_found(self, mock_get_current_user, mock_get_session, mock_db, mock_admin_user):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = result_mock

        reservation_id = uuid4()
        with pytest.raises(HTTPException) as exc:
            await router.routes[0].endpoint(reservation_id, mock_admin_user, mock_db)
        
        assert exc.value.status_code == 404
        assert "Нет записи с таким id" in exc.value.detail

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    async def test_verify_user_success(self, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_regular_user):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_regular_user
        mock_db.execute.return_value = result_mock

        user_id = mock_regular_user.id
        result = await router.routes[1].endpoint(user_id, mock_admin_user, mock_db)

        assert mock_regular_user.verified is True
        assert mock_db.commit.called

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    async def test_verify_user_not_admin(self, mock_get_current_user, mock_get_session, mock_db, mock_regular_user):
        mock_get_current_user.return_value = mock_regular_user
        mock_get_session.return_value = mock_db

        user_id = uuid4()
        with pytest.raises(HTTPException) as exc:
            await router.routes[1].endpoint(user_id, mock_regular_user, mock_db)
        
        assert exc.value.status_code == 403
        assert "Доступ запрещен" in exc.value.detail

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.ReservationRepository")
    async def test_delete_reservation_success(self, mock_repo, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_reservation):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_repo.return_value.update_statuses = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_reservation
        mock_db.execute.return_value = result_mock

        reservation_id = mock_reservation.id
        response = await router.routes[2].endpoint(reservation_id, mock_admin_user, mock_db)

        mock_repo.return_value.update_statuses.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_reservation)
        mock_db.commit.assert_called_once()
        assert response.status_code == 204

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.ReservationRepository")
    async def test_delete_reservation_not_found(self, mock_repo, mock_get_current_user, mock_get_session, mock_db, mock_admin_user):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_repo.return_value.update_statuses = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = result_mock

        reservation_id = uuid4()
        response = await router.routes[2].endpoint(reservation_id, mock_admin_user, mock_db)

        assert response.status_code == 204
        mock_db.delete.assert_not_called()

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.ReservationRepository")
    @patch("server.routers.admin_panel.make_timezone_naive")
    async def test_update_reservation_success(self, mock_make_naive, mock_repo, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_reservation):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_repo.return_value.update_statuses = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = mock_reservation
        mock_db.execute.return_value = result_mock

        mock_make_naive.side_effect = lambda x: x

        new_start = datetime.now(timezone.utc)
        new_end = datetime.now(timezone.utc)
        update_data = ReservationUpdate(start=new_start, end=new_end, status="active")

        reservation_id = mock_reservation.id
        result = await router.routes[3].endpoint(reservation_id, update_data, mock_admin_user, mock_db)

        mock_repo.return_value.update_statuses.assert_called_once()
        mock_make_naive.assert_any_call(new_start)
        mock_make_naive.assert_any_call(new_end)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_reservation)
        assert result == mock_reservation

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.ReservationManager")
    @patch("server.routers.admin_panel.ReservationRepository")
    async def test_create_reservation_success(self, mock_repo, mock_manager, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_reservation):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_repo.return_value.update_statuses = AsyncMock()
        mock_manager.return_value.create_reservation = AsyncMock(return_value=mock_reservation)

        user_id = uuid4()
        seat_id = uuid4()
        start = datetime.now(timezone.utc)
        end = datetime.now(timezone.utc)
        reservation_data = ReservationCreate(user_id=user_id, seat_id=seat_id, start=start, end=end)

        result = await router.routes[4].endpoint(reservation_data, mock_admin_user, mock_db)

        mock_repo.return_value.update_statuses.assert_called_once()
        mock_manager.return_value.create_reservation.assert_called_once_with(
            str(user_id), start, end, str(seat_id)
        )
        assert result == mock_reservation

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.ReservationManager")
    @patch("server.routers.admin_panel.ReservationRepository")
    async def test_get_reservations_success(self, mock_repo, mock_manager, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_reservation, mock_seat):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_repo.return_value.update_statuses = AsyncMock()

        all_reservations_result = MagicMock()
        all_reservations_result.scalars.return_value.all.return_value = [mock_reservation, MagicMock()]
        
        seat_query_result = MagicMock()
        seat_query_result.scalars.return_value.first.return_value = mock_seat

        mock_db.execute.side_effect = [all_reservations_result, seat_query_result, seat_query_result]

        result = await router.routes[6].endpoint(mock_admin_user, mock_db)

        mock_repo.return_value.update_statuses.assert_called_once()
        result_list = list(result)
        assert len(result_list) == 2
        for res in result_list:
            assert hasattr(res, "seat_name")
            assert res.seat_name == mock_seat.name

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.TicketRepository")
    async def test_get_all_tickets(self, mock_ticket_repo, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_ticket, mock_seat):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        tickets = [mock_ticket, MagicMock()]

        get_tickets_result = MagicMock()
        get_tickets_result.scalars.return_value.all.return_value = tickets
        mock_ticket_repo.return_value.get_tickets = AsyncMock(return_value=get_tickets_result)

        seat_result = MagicMock()
        seat_result.scalars.return_value.first.return_value = mock_seat
        mock_db.execute.return_value = seat_result

        result = await router.routes[7].endpoint(mock_admin_user, mock_db)

        mock_ticket_repo.return_value.get_tickets.assert_called_once()
        assert len(result) == len(tickets)
        for ticket in result:
            assert "seat_name" in ticket

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    async def test_get_all_users(self, mock_get_current_user, mock_get_session, mock_db, mock_admin_user):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        result_mock = MagicMock()
        users = [mock_admin_user, MagicMock(), MagicMock()]
        result_mock.scalars.return_value.all.return_value = users
        mock_db.execute.return_value = result_mock

        result = await router.routes[8].endpoint(mock_admin_user, mock_db)

        assert result == users
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.UserRepository")
    async def test_update_user_success(self, mock_user_repo, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_regular_user):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_user_repo.return_value.get_by_id = AsyncMock(return_value=mock_regular_user)
        mock_user_repo.return_value.get_by_email = AsyncMock(return_value=None)
        mock_user_repo.return_value.update_user = AsyncMock(return_value=mock_regular_user)

        update_data = UserUpdateAdmin(first_name="Updated Name", role="admin", email="updated@example.com")

        user_id = mock_regular_user.id
        result = await router.routes[9].endpoint(user_id, update_data, mock_admin_user, mock_db)

        mock_user_repo.return_value.get_by_id.assert_called_once_with(user_id)
        mock_user_repo.return_value.update_user.assert_called_once()
        assert result == mock_regular_user

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.TicketRepository")
    async def test_update_ticket_status(self, mock_ticket_repo, mock_get_current_user, mock_get_session, mock_db, mock_admin_user, mock_ticket):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_ticket_repo.return_value.update_ticket_status = AsyncMock(return_value=mock_ticket)

        ticket_id = mock_ticket.id
        status_update = TicketStatusUpdate(status="resolved")

        result = await router.routes[10].endpoint(ticket_id, status_update, mock_admin_user, mock_db)

        mock_ticket_repo.return_value.update_ticket_status.assert_called_once_with(ticket_id, status_update.status)
        assert result == mock_ticket

    @pytest.mark.asyncio
    @patch("server.routers.admin_panel.get_session")
    @patch("server.routers.admin_panel.get_current_user_from_cookie")
    @patch("server.routers.admin_panel.ImageStorage")
    async def test_upload_default_avatar(self, mock_image_storage_cls, mock_get_current_user, mock_get_session, mock_db, mock_admin_user):
        mock_get_current_user.return_value = mock_admin_user
        mock_get_session.return_value = mock_db

        mock_image_storage = MagicMock()
        mock_image_storage_cls.return_value = mock_image_storage
        mock_image_storage.upload_default_avatar.return_value = "avatar123.jpg"
        mock_image_storage.get_image_url.return_value = "http://example.com/avatar123.jpg"

        mock_file = MagicMock()

        result = await router.routes[11].endpoint(mock_file, mock_admin_user)

        mock_image_storage.upload_default_avatar.assert_called_once_with(mock_file)
        mock_image_storage.get_image_url.assert_called_once_with("avatar123.jpg")
        assert result == {"image_id": "avatar123.jpg", "url": "http://example.com/avatar123.jpg"}
