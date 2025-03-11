from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from server.utils.datetime_utils import make_timezone_naive

from server.models.ticket import Ticket
from server.schemas.ticket import TicketCreate


class TicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(self, user_id: str,
                            seat_name: str | None,
                            seat_id: str | None,
                            reservation_id: str | None,
                            ticket_data: TicketCreate):
        db_ticket = Ticket(
            user_id=user_id,
            reservation_id=reservation_id,
            seat_id=seat_id,
            seat_name=seat_name,
            theme=ticket_data.theme,
            message=ticket_data.message,
        )
        self.db.add(db_ticket)
        await self.db.commit()
        await self.db.refresh(db_ticket)
        return db_ticket

    async def get_ticket_by_id(self, ticket_id):
        return await self.db.get(Ticket, ticket_id)

    async def get_tickets(self):
        return await self.db.execute(select(Ticket))

    async def update_ticket_status(self, ticket_id, status):
        ticket = await self.get_ticket_by_id(ticket_id)
        ticket.status = status
        await self.db.commit()
        return ticket

    async def get_user_tickets(self, user_id):
        return await self.db.execute(select(Ticket).where(Ticket.user_id == user_id))

    async def get_unanswered_tickets(self):
        return await self.db.execute(select(Ticket).where(Ticket.status == None))
