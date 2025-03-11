import threading
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.backend.database import get_session
from server.dependencies.auth_dependencies import get_current_user_from_cookie
from server.models.reservation import Reservation
from server.models.seat import Seat
from server.schemas.reservation import ReservationCreate, ReservationBase, ReservationOut
from server.repositories.reservation import ReservationRepository
from server.services.reservation import ReservationManager
from server.utils.datetime_utils import make_timezone_naive
from server.utils.exceptions import SeatIsNotAvailableError
from server.schemas.reservation import ReservationUpdate

from uuid import UUID

from server.utils.exceptions import UserAlreadyHasActiveReservationError

router = APIRouter(prefix="/reservations", tags=["reservations"])
ads_lock = threading.Lock()


@router.post("", response_model=ReservationBase, status_code=status.HTTP_201_CREATED)
async def create_reservation(reservation: ReservationCreate, db: AsyncSession = Depends(get_session),
                             user=Depends(get_current_user_from_cookie)):
    if reservation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You can't create reservation for another user")

    reservation.start = make_timezone_naive(reservation.start)
    reservation.end = make_timezone_naive(reservation.end)

    print(reservation.start, reservation.end)

    try:
        new_reservation = await ReservationManager(db).create_reservation(
            str(reservation.user_id), reservation.start, reservation.end, str(reservation.seat_id)
        )
        return new_reservation
    except SeatIsNotAvailableError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat is not available")
    except UserAlreadyHasActiveReservationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has active reservation")


@router.get("", response_model=list[ReservationOut], summary="Получение списка всех бронирований пользователя")
async def get_reservations(db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user_from_cookie)):
    await ReservationRepository(db).update_statuses()
    reservation_repo = ReservationRepository(db)
    reservations = await reservation_repo.get_reservations_by_user_id(current_user.id)
    return reversed(reservations)


@router.get("/active", response_model=ReservationOut, summary="Получение активной брони пользователя")
async def get_active_reservation(db: AsyncSession = Depends(get_session),
                                 current_user=Depends(get_current_user_from_cookie)):
    await ReservationRepository(db).update_statuses()
    reservation = await ReservationManager(db).get_active_user_reservation(current_user.id)

    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нет активных броней")

    return reservation


@router.get("/maximum-available-time", response_model=dict,
            summary="Получение максимально доступного времени для переноса брони")
async def get_maximum_available_time_endpoint(
        start_time: datetime,
        db: AsyncSession = Depends(get_session),
        current_user=Depends(get_current_user_from_cookie)
):
    naive_start_time = make_timezone_naive(start_time)
    manager = ReservationManager(db)
    max_time = await manager.get_maximum_available_time(current_user.id, naive_start_time)
    if not max_time:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нет доступного времени для переноса брони")
    if max_time == -58:
        return {"maximum_available_time": -1}
    return {"maximum_available_time": max_time.isoformat()}


@router.get("/{reservation_id}", response_model=ReservationBase, summary="Получение бронирования по id")
async def get_reservation(reservation_id: UUID, db: AsyncSession = Depends(get_session),
                          current_user=Depends(get_current_user_from_cookie)):
    await ReservationRepository(db).update_statuses()
    reservation_repo = ReservationRepository(db)
    reservation = await reservation_repo.get_by_id(reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    if reservation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't get this reservation")
    return reservation


@router.patch("/{reservation_id}", response_model=ReservationUpdate)
async def update_reservation(reservation_id: UUID, reservation: ReservationUpdate,
                             db: AsyncSession = Depends(get_session),
                             current_user=Depends(get_current_user_from_cookie)):
    await ReservationRepository(db).update_statuses()
    reservation_repo = ReservationRepository(db)
    reservation_db = await reservation_repo.get_by_id(reservation_id)
    if not reservation_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")
    if reservation_db.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can't update this reservation")
    updated_reservation = await reservation_repo.update_reservation(reservation_id, reservation)
    return updated_reservation


@router.get("/{reservation_id}", response_model=ReservationOut, summary="Получение брони")
async def get_reservation_by_id(reservation_id: UUID,
                                db: AsyncSession = Depends(get_session)):
    await ReservationRepository(db).update_statuses()
    reservation = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = reservation.scalars().first()

    if reservation is None:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    seat = await db.execute(select(Seat).where(Seat.id == reservation.seat_id))
    seat = seat.scalars().first()
    reservation.seat_name = seat.name

    return reservation
