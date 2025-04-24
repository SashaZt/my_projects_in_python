# app/api/reservation_routes.py
from typing import Any, Dict, List, Optional

from app.core.dependencies import get_db
from app.schemas.reservation import (
    ReservationCreate,
    ReservationFilter,
    ReservationResponse,
    ReservationUpdate,
)
from app.services.reservation_service import ReservationService
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# Create router
router = APIRouter(
    prefix="/easyms/reservations",
    tags=["reservations"],
    responses={404: {"description": "Not found"}},
)


def adapt_booking_com_data(reservation_data, reservation_id=None):
    """Адаптирует данные от Booking.com для системы бронирования"""
    # Для ReservationUpdate id передается как параметр
    is_booking_id = False

    if reservation_id is not None:
        is_booking_id = reservation_id.isdigit()
    elif hasattr(reservation_data, "id"):
        is_booking_id = reservation_data.id.isdigit()

    # Проверяем, является ли бронирование от Booking.com
    if is_booking_id:
        logger.debug(
            f"Адаптация данных Booking.com для бронирования {reservation_id or getattr(reservation_data, 'id', 'unknown')}"
        )

        # Адаптируем данные клиента
        if (
            hasattr(reservation_data, "customer")
            and reservation_data.customer is not None
        ):
            # Создаем словарь с нужными полями
            customer_data = {
                "name": getattr(reservation_data.customer, "name", ""),
                "email": getattr(reservation_data.customer, "email", ""),
                "telephone": getattr(reservation_data.customer, "telephone", ""),
                "remarks": getattr(reservation_data.customer, "remarks", ""),
            }

            # Используем CustomerBase для создания правильного объекта
            from app.schemas.reservation import CustomerBase

            reservation_data.customer = CustomerBase(**customer_data)

        # Проверяем наличие обязательных полей
        if (
            not hasattr(reservation_data, "responsibleUserId")
            or reservation_data.responsibleUserId is None
        ):
            reservation_data.responsibleUserId = 1203

    return reservation_data


@router.post("/", response_model=ReservationResponse, status_code=201)
async def create_reservation(
    reservation: ReservationCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new reservation."""
    try:
        logger.debug(f"Создание бронирования с ID: {reservation.id}")

        # Адаптируем данные Booking.com
        reservation = adapt_booking_com_data(reservation)

        result = await ReservationService.create_reservation(db, reservation)
        return result
    except Exception as e:
        logger.error(f"Error in create_reservation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create reservation: {str(e)}"
        )


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(reservation_id: str, db: AsyncSession = Depends(get_db)):
    """Get a reservation by ID."""
    try:
        logger.debug(f"Получение бронирования с ID: {reservation_id}")
        result = await ReservationService.get_reservation(db, reservation_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Reservation with ID {reservation_id} not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_reservation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve reservation: {str(e)}"
        )


@router.get("/", response_model=List[ReservationResponse])
async def get_reservations(
    id: Optional[str] = None,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    responsible_user_id: Optional[int] = None,
    booked_at_from: Optional[int] = None,
    booked_at_to: Optional[int] = None,
    arrival_from: Optional[int] = None,
    arrival_to: Optional[int] = None,
    departure_from: Optional[int] = None,
    departure_to: Optional[int] = None,
    customer_name: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all reservations with optional filters."""
    try:
        logger.debug("Получение списка бронирований с фильтрами")
        # Create filter object from query parameters
        filters = ReservationFilter(
            id=id,
            organizationId=organization_id,
            status=status,
            source=source,
            responsibleUserId=responsible_user_id,
            bookedAt_from=booked_at_from,
            bookedAt_to=booked_at_to,
            arrival_from=arrival_from,
            arrival_to=arrival_to,
            departure_from=departure_from,
            departure_to=departure_to,
            customer_name=customer_name,
        )

        results = await ReservationService.get_reservations(db, filters, skip, limit)
        logger.debug(f"Найдено {len(results)} бронирований")
        return results
    except Exception as e:
        logger.error(f"Error in get_reservations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve reservations: {str(e)}"
        )


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: str,
    reservation: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a reservation."""
    try:
        logger.debug(f"Обновление бронирования с ID: {reservation_id}")

        # Адаптируем данные Booking.com
        if reservation_id.isdigit():
            reservation = adapt_booking_com_data(reservation, reservation_id)
            logger.debug(
                f"Данные Booking.com адаптированы для обновления: {reservation_id}"
            )

        result = await ReservationService.update_reservation(
            db, reservation_id, reservation
        )
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Reservation with ID {reservation_id} not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении бронирования: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось обновить бронирование: {str(e)}"
        )


@router.delete("/{reservation_id}", status_code=204)
async def delete_reservation(reservation_id: str, db: AsyncSession = Depends(get_db)):
    """Удалить бронирование."""
    try:
        logger.debug(f"Удаление бронирования с ID: {reservation_id}")
        result = await ReservationService.delete_reservation(db, reservation_id)
        if not result:
            raise HTTPException(
                status_code=404, detail=f"Бронирование с ID {reservation_id} не найдено"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при удалении бронирования: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось удалить бронирование: {str(e)}"
        )


@router.post("/bulk", status_code=201)
async def create_bulk_reservations(
    reservations: List[ReservationCreate], db: AsyncSession = Depends(get_db)
):
    """Массовое создание бронирований."""
    try:
        logger.debug(f"Массовое создание {len(reservations)} бронирований")
        results = []
        for reservation_data in reservations:
            logger.debug(f"Обработка бронирования {reservation_data.id}")

            # Адаптируем данные Booking.com
            reservation_data = adapt_booking_com_data(reservation_data)

            result = await ReservationService.create_reservation(db, reservation_data)
            results.append(result["id"])

        logger.info(f"Успешно создано {len(results)} бронирований")
        return {"created_reservations": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Ошибка при массовом создании бронирований: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при массовом создании бронирований: {str(e)}",
        )


@router.put("/status/{reservation_id}", response_model=ReservationResponse)
async def update_reservation_status(
    reservation_id: str, status: str, db: AsyncSession = Depends(get_db)
):
    """Обновить статус бронирования."""
    try:
        logger.debug(f"Обновление статуса бронирования {reservation_id} на {status}")

        # Создаем данные для обновления только статуса
        update_data = ReservationUpdate(status=status)

        result = await ReservationService.update_reservation(
            db, reservation_id, update_data
        )
        if not result:
            raise HTTPException(
                status_code=404, detail=f"Бронирование с ID {reservation_id} не найдено"
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса бронирования: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Не удалось обновить статус бронирования: {str(e)}"
        )
