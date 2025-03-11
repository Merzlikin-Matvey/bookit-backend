from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Response, Body, Path, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from server.models.seat import Seat
from server.models.user import User
from server.repositories.reservation import ReservationRepository
from server.repositories.ticket import TicketRepository
from server.repositories.user import UserRepository
from server.schemas.ticket import TicketStatusUpdate, TicketBase
from server.schemas.user import UserOut, UserBase, UserUpdateAdmin
from server.backend.database import get_session
from server.dependencies.auth_dependencies import get_current_user_from_cookie

from server.models.reservation import Reservation
from server.schemas.reservation import ReservationUpdate, ReservationBase, ReservationCreate, ReservationOut
from server.services.image_storage import ImageStorage
from server.services.reservation import ReservationManager
from server.utils.datetime_utils import make_timezone_naive

import uuid

from server.utils.exceptions import SeatIsNotAvailableError
from server.utils.exceptions import UserAlreadyHasActiveReservationError

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/check_qr/{reservation_id}", summary="Проверка QR-кода админом")
async def check_qr(reservation_id: Annotated[uuid.UUID, Path()],
                   current_user: UserOut = Depends(get_current_user_from_cookie),
                   db: AsyncSession = Depends(get_session)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    exists = await db.execute(select(Reservation).filter(Reservation.id == reservation_id))
    exists = exists.scalars().first()

    if exists is None:
        raise HTTPException(status_code=404, detail="Нет записи с таким id")

    user = await db.execute(select(User).where(User.id == exists.user_id))
    user = user.scalars().first()

    if not user.verified:
        return Response(status_code=424, content={"detail": "Необходима верификация пользователя"})

    exists.status = "active"
    await db.commit()

    return


@router.post("/verify_user/{user_id}", summary="Верификация пользователя админом")
async def verify_user(user_id: Annotated[uuid.UUID, Path()],
                      current_user: UserOut = Depends(get_current_user_from_cookie),
                      db: AsyncSession = Depends(get_session)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    user = await db.execute(select(User).where(User.id == user_id))
    user = user.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.verified:
        return

    user.verified = True
    await db.commit()
    return


@router.delete("/reservation/{reservation_id}", summary="Удаление брони админом")
async def delete_reservation(reservation_id: Annotated[uuid.UUID, Path()],
                             current_user: UserOut = Depends(get_current_user_from_cookie),
                             db: AsyncSession = Depends(get_session)):
    await ReservationRepository(db).update_statuses()
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    reservation = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = reservation.scalars().first()

    if reservation is None:
        return Response(status_code=204)

    await db.delete(reservation)
    await db.commit()
    return Response(status_code=204)


@router.patch("/reservation/{reservation_id}", summary="Редактирование брони админом",
              response_model=ReservationUpdate)
async def update_reservation(reservation_id: Annotated[uuid.UUID, Path()],
                             reservation: Annotated[ReservationUpdate, Body()],
                             current_user: UserOut = Depends(get_current_user_from_cookie),
                             db: AsyncSession = Depends(get_session)):
    await ReservationRepository(db).update_statuses()
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    res_query = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation_db = res_query.scalars().first()

    if reservation_db is None:
        raise HTTPException(status_code=404, detail="Бронь не найдена")

    if reservation.start is not None:
        reservation_db.start = make_timezone_naive(reservation.start)
    if reservation.end is not None:
        reservation_db.end = make_timezone_naive(reservation.end)
    if reservation.status is not None:
        reservation_db.status = reservation.status

    await db.commit()
    await db.refresh(reservation_db)

    return reservation_db


@router.post("/reservation/create", summary="Cоздание брони админом",
             response_model=ReservationBase, status_code=201)
async def create_reservation(reservation: Annotated[ReservationCreate, Body()],
                             current_user: UserOut = Depends(get_current_user_from_cookie),
                             db: AsyncSession = Depends(get_session)):
    await ReservationRepository(db).update_statuses()
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    try:
        new_reservation = await ReservationManager(db).create_reservation(
            str(reservation.user_id), reservation.start, reservation.end, str(reservation.seat_id)
        )
        return new_reservation
    except SeatIsNotAvailableError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat is not available")
    except UserAlreadyHasActiveReservationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has active reservation")


@router.get("/reservation/{reservation_id}", summary="Получение брони админом",
            response_model=ReservationBase, status_code=200)
async def get_reservation(reservation_id: Annotated[uuid.UUID, Path()],
                          current_user: UserOut = Depends(get_current_user_from_cookie),
                          db: AsyncSession = Depends(get_session)):
    await ReservationRepository(db).update_statuses()
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    reservation_db = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation_db = reservation_db.scalars().first()

    if reservation_db is None:
        return HTTPException(status_code=404, detail="Бронь не найдена")

    return reservation_db


@router.get("/reservations", summary="Получение всех броней админом",
            response_model=list[ReservationOut], status_code=200)
async def get_all_reservations(current_user: UserOut = Depends(get_current_user_from_cookie),
                               db: AsyncSession = Depends(get_session)):
    await ReservationRepository(db).update_statuses()
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    all_reservations = await db.execute(select(Reservation))
    all_reservations = all_reservations.scalars().all()

    answer = []
    for reservation in all_reservations:
        seat = await db.execute(select(Seat).where(Seat.id == reservation.seat_id))
        seat = seat.scalars().first()
        reservation.seat_name = seat.name
        answer.append(reservation)

    return reversed(answer)


@router.get("/tickets", response_model=List[TicketBase], summary="Получение всех тикетов (для админа)")
async def get_all_tickets(
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    ticket_repo = TicketRepository(db)
    result = await ticket_repo.get_tickets()
    tickets = result.scalars().all()

    answer = []
    for ticket in tickets:
        seat = await db.execute(select(Seat).where(Seat.id == ticket.seat_id))
        seat = seat.scalars().first()
        if seat:
            seat_name = seat.name
        else:
            seat_name = "Test name"
        d = {
            "id": ticket.id,
            "user_id": ticket.user_id,
            "reservation_id": ticket.reservation_id,
            "seat_id": ticket.seat_id,
            "theme": ticket.theme,
            "message": ticket.message,
            "status": ticket.status,
            "made_on": ticket.made_on,
            "seat_name": seat_name
        }
        answer.append(d)

    return reversed(answer)


@router.get("/users", response_model=List[UserOut], summary="Получение всех пользователей (для админа)")
async def get_all_users(
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    all_users = await db.execute(select(User))
    all_users = all_users.scalars().all()
    return all_users


@router.patch("/user/{user_id}", response_model=UserOut, summary="Редактирование пользователя (для админа)")
async def update_user(
        user_id: Annotated[uuid.UUID, Path()],
        user_update: UserUpdateAdmin,
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    user_repo = UserRepository(db)
    update_data = user_update.model_dump(exclude_unset=True)
    user = await user_repo.get_by_id(user_id)

    if "email" in update_data and update_data["email"] != user.email:
        existing_user = await user_repo.get_by_email(update_data["email"])
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    updated_user = await user_repo.update_user(user_id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return updated_user


@router.patch("/ticket/{ticket_id}/status", response_model=TicketStatusUpdate,
              summary="Обновление статуса тикета (для админа)")
async def update_ticket_status(
        ticket_id: uuid.UUID,
        status_update: TicketStatusUpdate,
        current_user: UserOut = Depends(get_current_user_from_cookie),
        db: AsyncSession = Depends(get_session)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    ticket_repo = TicketRepository(db)
    updated_ticket = await ticket_repo.update_ticket_status(ticket_id, status_update.status)
    if not updated_ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    return updated_ticket


@router.post("/default_avatar", summary="Загрузка аватара по умолчанию админом")
async def upload_default_avatar(
        image: UploadFile = File(...),
        current_user: UserOut = Depends(get_current_user_from_cookie)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    image_storage = ImageStorage()
    try:
        file_name = image_storage.upload_default_avatar(image)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"image_id": file_name, "url": image_storage.get_image_url(file_name)}
