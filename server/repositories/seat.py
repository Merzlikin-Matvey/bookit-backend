from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.seat import Seat
from server.models.reservation import Reservation
from server.schemas.seat import SeatCreate
from server.schemas.seat import SeatUpdate
from server.services.seats_manager import SeatsManager
from server.utils.datetime_utils import make_timezone_naive


class SeatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_seat(self, seat_data: SeatCreate):
        db_seat = Seat(
            name=seat_data.name,
            x=seat_data.x,
            y=seat_data.y,
            type=seat_data.type,
            has_water=seat_data.has_water,
            has_kitchen=seat_data.has_kitchen,
            is_quite=seat_data.is_quite,
            has_computer=seat_data.has_computer,
            has_smart_desk=seat_data.has_smart_desk,
            is_talk_room=seat_data.is_talk_room
        )
        self.db.add(db_seat)
        await self.db.commit()
        await self.db.refresh(db_seat)
        return db_seat

    async def get_by_id(self, seat_id: UUID):
        result = await self.db.execute(select(Seat).filter(Seat.id == seat_id))
        scalars_result = result.scalars()
        seat = scalars_result.first()
        return seat

    async def delete_seat(self, seat_id: UUID):
        result = await self.db.execute(select(Seat).filter(Seat.id == seat_id))
        scalars_result = result.scalars()
        seat = scalars_result.first()
        if not seat:
            return False
        await self.db.delete(seat)
        await self.db.commit()
        return True

    async def update_seat(self, seat_id: UUID, update_data: SeatUpdate):
        result = await self.db.execute(select(Seat).filter(Seat.id == seat_id))
        scalars_result = result.scalars()
        seat = scalars_result.first()
        if not seat:
            return None
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(seat, field, value)
        await self.db.commit()
        await self.db.refresh(seat)
        return seat

    async def get_all(self, start: datetime, end: datetime):
        seats_result = await self.db.execute(select(Seat))
        scalars_result = seats_result.scalars()
        seats = scalars_result.all()

        start_naive = make_timezone_naive(start)
        end_naive = make_timezone_naive(end)

        print(f"Original start: {start}, end: {end}")
        print(f"Naive start: {start_naive}, end: {end_naive}")
        
        res_result = await self.db.execute(
            select(Reservation).filter(Reservation.end > start_naive, Reservation.start < end_naive)
        )
        scalars_res = res_result.scalars()
        reservations = scalars_res.all()
        occupied_seat_ids = {reservation.seat_id for reservation in reservations if reservation.status in ['future', 'active']}

        for seat in seats:
            seat.is_available = seat.id not in occupied_seat_ids
        return seats
