from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import datetime
from server.models.reservation import Reservation
from server.models.seat import Seat
from server.utils.exceptions import UserAlreadyHasActiveReservationError


class ReservationManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def does_user_have_active_reservation(self, user_id) -> bool:
        now = datetime.datetime.utcnow()
        stmt = select(Reservation).filter(
            Reservation.user_id == user_id,
            Reservation.end > now,
            Reservation.status != "closed"
        )   
        result = await self.db.execute(stmt)
        reservation = result.scalars().first()
        return reservation is not None

    async def create_reservation(self, user_id: str, start: datetime.datetime, end: datetime.datetime, seat_id: str):
        if await self.does_user_have_active_reservation(user_id):  
            raise UserAlreadyHasActiveReservationError(user_id=user_id)
        db_reservation = Reservation(user_id=user_id, start=start, end=end, seat_id=seat_id)
        self.db.add(db_reservation)
        await self.db.commit()
        await self.db.refresh(db_reservation)
        return db_reservation

    async def get_active_user_reservation(self, user_id):
        now = datetime.datetime.utcnow()
        stmt = select(Reservation).filter(
            Reservation.user_id == user_id,
            Reservation.end > now,
            Reservation.status != "closed"
        )
        result = await self.db.execute(stmt)
        reservation = result.scalars().first()
        if reservation is not None:
            seat = await self.db.execute(select(Seat).where(Seat.id == reservation.seat_id))
            seat = seat.scalars().first()
            reservation.seat_name = seat.name
        return reservation

    async def get_maximum_available_time(self, user_id, start_time: datetime.datetime) -> datetime.datetime:
        stmt = select(Reservation.start).filter(
            Reservation.user_id != user_id,
            Reservation.start > start_time,
            Reservation.status != "closed"
        ).order_by(Reservation.start.asc()).limit(1)
        result = await self.db.execute(stmt)
        next_start = result.scalar()
        return next_start if next_start is not None else -58
