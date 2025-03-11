import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from server.models.reservation import Reservation


class SeatsManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_aware_dt(self, dt: datetime.datetime) -> datetime.datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)

    async def is_available(self, seat_id: UUID, start: datetime.datetime, end: datetime.datetime) -> bool:
        stmt = select(Reservation).where(Reservation.seat_id == seat_id)
        result = await self.db.execute(stmt)
        reservations = result.scalars().all()
        for reservation in reservations:
            aware_start = self._to_aware_dt(reservation.start)
            aware_end = self._to_aware_dt(reservation.end)
            if not (aware_end <= start or aware_start >= end):
                print("ID резервации", reservation.id)
                return False
        return True

    async def get_occupied_seats(self, start: datetime.datetime, end: datetime.datetime) -> list:
        result = await self.db.execute(select(Reservation))
        reservations = result.scalars().all()
        occupied_seats = set()
        for reservation in reservations:
            aware_start = self._to_aware_dt(reservation.start)
            aware_end = self._to_aware_dt(reservation.end)
            if not (aware_end <= start or aware_start >= end):
                occupied_seats.add(str(reservation.seat_id))
        return list(occupied_seats)

