from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from server.repositories.reservation import ReservationRepository
from server.repositories.seat import SeatRepository
from server.schemas.ticket import TicketCreate, TicketStatusUpdate, TicketOut
from server.repositories.ticket import TicketRepository
from server.backend.database import get_session
from server.dependencies.auth_dependencies import get_current_user_from_cookie
from server.schemas.user import UserOut
from server.repositories.user import UserRepository
from server.services.reservation import ReservationManager
from server.services.telegram import TelegramSender

router = APIRouter(prefix="/ticket", tags=["ticket"])


@router.post("", response_model=TicketOut, summary="Создание тикета пользователем")
async def create_ticket(
        ticket_data: TicketCreate,
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    ticket_repo = TicketRepository(db)

    user_id = current_user.id
    reservation = await ReservationManager(db).get_active_user_reservation(user_id)
    if not reservation:
        new_ticket = await ticket_repo.create_ticket(str(user_id), None, None, None, ticket_data)
    else:
        seat_id = reservation.seat_id
        seat_repository = SeatRepository(db)
        seat = await seat_repository.get_by_id(seat_id)
        new_ticket = await ticket_repo.create_ticket(user_id=str(user_id),
                                                     seat_name=seat.name,
                                                     seat_id=seat.id,
                                                     reservation_id=reservation.id,
                                                     ticket_data=ticket_data)

    telegram_sender = TelegramSender(db=db)
    await telegram_sender.send_ticket_to_all_admins(new_ticket)

    return new_ticket


@router.get("/my", response_model=list[TicketOut], summary="Получение тикетов текущего пользователя")
async def get_user_tickets(
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    ticket_repo = TicketRepository(db)
    result = await ticket_repo.get_user_tickets(current_user.id)
    tickets = result.scalars().all()
    return tickets
