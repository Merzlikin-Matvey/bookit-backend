import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.utils.datetime_utils import MOSCOW_TZ
from server.utils.exceptions import SeatIsNotAvailableError
from server.models.reservation import Reservation
from server.models.seat import Seat
from server.schemas.reservation import ReservationCreate
from server.schemas.reservation import ReservationUpdate
from server.services.seats_manager import SeatsManager
from server.utils.datetime_utils import make_timezone_naive

from uuid import UUID


class ReservationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reservation(self, reservation_data: ReservationCreate):
        manager = SeatsManager(self.db)

        start_time = reservation_data.start
        end_time = reservation_data.end
        
        if not await manager.is_available(
                reservation_data.seat_id,
                start_time,
                end_time
        ):
            raise SeatIsNotAvailableError(
                reservation_data.seat_id,
                start_time,
                end_time
            )

        start_naive = make_timezone_naive(start_time)
        end_naive = make_timezone_naive(end_time)

        status = "future"

        if end_naive < datetime.datetime.now():
            status = "did_not_come"

        db_reservation = Reservation(
            user_id=reservation_data.user_id,
            seat_id=reservation_data.seat_id,
            start=start_naive,
            end=end_naive,
            status=status
        )
        self.db.add(db_reservation)
        await self.db.commit()
        await self.db.refresh(db_reservation)
        return db_reservation

    async def get_by_id(self, reservation_id: UUID):
        result = await self.db.execute(select(Reservation).filter(Reservation.id == reservation_id))
        return result.scalars().first()

    async def delete_reservation(self, reservation_id: UUID):
        result = await self.db.execute(select(Reservation).filter(Reservation.id == reservation_id))
        reservation = result.scalars().first()
        if not reservation:
            return False
        await self.db.delete(reservation)
        await self.db.commit()
        return True

    async def get_reservations_by_user_id(self, user_id: UUID):
        result = await self.db.execute(select(Reservation).filter(Reservation.user_id == user_id))
        reservations = result.scalars().all()
        answer = []
        for reservation in reservations:
            seat = await self.db.execute(select(Seat).where(Seat.id == reservation.seat_id))
            seat = seat.scalars().first()
            reservation.seat_name = seat.name
            answer.append(reservation)
        return answer

    async def update_reservation(self, reservation_id: UUID, reservation_data: ReservationUpdate):
        result = await self.db.execute(select(Reservation).filter(Reservation.id == reservation_id))
        reservation = result.scalars().first()
        if not reservation:
            return None
        
        update_data = reservation_data.model_dump(exclude_unset=True)

        if 'start' in update_data and update_data['start'] is not None:
            update_data['start'] = make_timezone_naive(update_data['start'])
        
        if 'end' in update_data and update_data['end'] is not None:
            update_data['end'] = make_timezone_naive(update_data['end'])
            
        for field, value in update_data.items():
            setattr(reservation, field, value)
            
        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def update_statuses(self):
        result = await self.db.execute(select(Reservation))
        reservations = result.scalars().all()
        now = datetime.datetime.now(tz=MOSCOW_TZ).replace(tzinfo=None)
        for reservation in reservations:
            print(reservation.end, now)
            if reservation.status == "future" and reservation.end < now:
                reservation.status = "did_not_come"
        await self.db.commit()
        return True

    async def get_all_reservations(self):
        """Retrieve all reservations"""
        result = await self.db.execute(select(Reservation))
        reservations = result.scalars().all()
        return reservations