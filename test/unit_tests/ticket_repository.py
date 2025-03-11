import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from server.repositories.ticket import TicketRepository
from server.models.ticket import Ticket
from server.schemas.ticket import TicketCreate
from server.schemas.ticket import TicketStatusEnum
from server.schemas.ticket import TicketThemeEnum


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
    db.get = AsyncMock()
    return db


@pytest.fixture
def mock_ticket():
    """Create a mock Ticket object"""
    ticket = MagicMock()
    ticket.id = uuid4()
    ticket.user_id = str(uuid4())
    ticket.seat_id = str(uuid4())
    ticket.seat_name = "Test Seat"
    ticket.reservation_id = str(uuid4())
    ticket.theme = "Test Ticket"
    ticket.message = "This is a test ticket"
    ticket.status = None
    return ticket


class TestTicketRepository:

    @pytest.mark.asyncio
    async def test_create_ticket(self, mock_db):
        """Test creating a new ticket"""
        repo = TicketRepository(mock_db)
        user_id = str(uuid4())
        seat_name = "Test Seat"
        seat_id = str(uuid4())
        reservation_id = str(uuid4())
        
        ticket_data = TicketCreate(
            theme=TicketThemeEnum.OTHER,
            message="This is a test ticket"
        )
        
        result = await repo.create_ticket(user_id, seat_name, seat_id, reservation_id, ticket_data)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        created_ticket = mock_db.add.call_args[0][0]
        assert created_ticket.user_id == user_id
        assert created_ticket.seat_name == seat_name
        assert created_ticket.seat_id == seat_id
        assert created_ticket.reservation_id == reservation_id
        assert created_ticket.theme == ticket_data.theme
        assert created_ticket.message == ticket_data.message
        assert result == created_ticket

    @pytest.mark.asyncio
    async def test_get_ticket_by_id(self, mock_db, mock_ticket):
        """Test retrieving a ticket by ID"""
        repo = TicketRepository(mock_db)
        ticket_id = mock_ticket.id
        mock_db.get.return_value = mock_ticket
        
        result = await repo.get_ticket_by_id(ticket_id)
        
        mock_db.get.assert_called_once_with(Ticket, ticket_id)
        assert result == mock_ticket

    @pytest.mark.asyncio
    async def test_get_tickets(self, mock_db, mock_ticket):
        """Test retrieving all tickets"""
        repo = TicketRepository(mock_db)
        mock_tickets = [mock_ticket, MagicMock(), MagicMock()]
        mock_db.execute.return_value = mock_tickets
        
        result = await repo.get_tickets()
        
        mock_db.execute.assert_called_once()
        assert result == mock_tickets

    @pytest.mark.asyncio
    async def test_update_ticket_status(self, mock_db, mock_ticket):
        """Test updating a ticket's status"""
        repo = TicketRepository(mock_db)
        ticket_id = mock_ticket.id
        new_status = "resolved"
        mock_db.get.return_value = mock_ticket
        
        result = await repo.update_ticket_status(ticket_id, new_status)
        
        mock_db.get.assert_called_once_with(Ticket, ticket_id)
        mock_db.commit.assert_called_once()
        assert mock_ticket.status == new_status
        assert result == mock_ticket

    @pytest.mark.asyncio
    async def test_get_user_tickets(self, mock_db, mock_ticket):
        """Test retrieving tickets for a specific user"""
        repo = TicketRepository(mock_db)
        user_id = mock_ticket.user_id
        user_tickets = [mock_ticket, MagicMock()]
        mock_db.execute.return_value = user_tickets
        
        result = await repo.get_user_tickets(user_id)
        
        mock_db.execute.assert_called_once()
        assert result == user_tickets

    @pytest.mark.asyncio
    async def test_get_unanswered_tickets(self, mock_db, mock_ticket):
        """Test retrieving unanswered tickets"""
        repo = TicketRepository(mock_db)
        mock_ticket.status = None
        unanswered_tickets = [mock_ticket, MagicMock()]
        mock_db.execute.return_value = unanswered_tickets
        
        result = await repo.get_unanswered_tickets()
        
        mock_db.execute.assert_called_once()
        assert result == unanswered_tickets
