from typing import List
from uuid import UUID
from datetime import date, time, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.backend.database import get_session
from server.dependencies.auth_dependencies import get_current_user_from_cookie
from server.repositories.seat import SeatRepository
from server.schemas.seat import SeatCreate, SeatOut, SeatUpdate
from server.schemas.user import UserOut
from server.utils.datetime_utils import make_timezone_aware

router = APIRouter(prefix="/seat", tags=["seat"])


@router.post("", response_model=SeatOut, summary="Создание места")
async def create_seat_endpoint(seat_data: SeatCreate, current_user: UserOut = Depends(get_current_user_from_cookie),
                               db: AsyncSession = Depends(get_session)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    seat = await SeatRepository(db).create_seat(seat_data)
    return seat


@router.patch("/{seat_id}", response_model=SeatUpdate, summary="Редактирование места")
async def update_seat_endpoint(seat_id: UUID, seat_data: SeatUpdate,
                               current_user: UserOut = Depends(get_current_user_from_cookie),
                               db: AsyncSession = Depends(get_session)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    seat = await SeatRepository(db).update_seat(seat_id, seat_data)
    if not seat:
        raise HTTPException(status_code=404, detail="Место не найдено")
    return seat


@router.delete("/{seat_id}", summary="Удаление места")
async def delete_seat_endpoint(seat_id: UUID, current_user: UserOut = Depends(get_current_user_from_cookie),
                               db: AsyncSession = Depends(get_session)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    success = await SeatRepository(db).delete_seat(seat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Место не найдено")
    return Response(status_code=204)


@router.get("/{seat_id}", response_model=SeatOut, summary="Получение места")
async def get_seat_endpoint(seat_id: UUID, db: AsyncSession = Depends(get_session)):
    seat = await SeatRepository(db).get_by_id(seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail="Место не найдено")
    return seat


@router.get("", response_model=List[SeatOut], summary="Получение информации о местах в заданный временной промежуток")
async def get_seats(
        start: datetime = Query(..., description="Start time (UTC)"),
        end: datetime = Query(..., description="End time (UTC)"),
        db: AsyncSession = Depends(get_session)
):
    start = make_timezone_aware(start)
    end = make_timezone_aware(end)
    
    print(f"API received start: {start}, end: {end}")
    
    seats = await SeatRepository(db).get_all(start, end)
    if not seats:
        return []
    return seats
