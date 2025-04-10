# app/services/reservation_service.py
import time
import uuid
from typing import Any, Dict, List, Optional

from app.models.reservation import Customer, Reservation, RoomReservation
from app.schemas.reservation import (
    ReservationCreate,
    ReservationFilter,
    ReservationUpdate,
)
from loguru import logger
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ReservationService:
    """Service for handling reservation operations."""

    @staticmethod
    async def create_reservation(
        db: AsyncSession, reservation_data: ReservationCreate
    ) -> Dict[str, Any]:
        """Create a new reservation in the database."""
        try:
            logger.debug(f"Начало создания бронирования с ID: {reservation_data.id}")

            # Проверяем, существует ли уже бронирование с таким ID
            exist_query = select(Reservation).where(
                Reservation.id == reservation_data.id
            )
            result = await db.execute(exist_query)
            existing_reservation = result.scalars().first()

            if existing_reservation:
                logger.info(f"Бронирование с ID {reservation_data.id} уже существует")
                # Возвращаем существующее бронирование
                return await ReservationService.get_reservation(db, reservation_data.id)

            # Set current timestamp if not provided
            current_time = int(time.time() * 1000)
            if not reservation_data.bookedAt:
                reservation_data.bookedAt = current_time
                logger.debug(f"Установлено время bookedAt: {current_time}")
            if not reservation_data.modifiedAt:
                reservation_data.modifiedAt = current_time
                logger.debug(f"Установлено время modifiedAt: {current_time}")

            logger.debug("Создание объекта бронирования")
            # Create customer
            customer_id = str(uuid.uuid4())
            customer = Customer(
                id=customer_id,
                name=reservation_data.customer.name,
                email=reservation_data.customer.email,
                telephone=reservation_data.customer.telephone,
                remarks=reservation_data.customer.remarks,
            )
            db.add(customer)

            logger.debug("Создание объектов номеров")

            # Create reservation
            reservation = Reservation(
                id=reservation_data.id,
                organizationId=reservation_data.organizationId,
                customerId=customer_id,
                status=reservation_data.status,
                services=reservation_data.services,
                bookedAt=reservation_data.bookedAt,
                modifiedAt=reservation_data.modifiedAt,
                source=reservation_data.source,
                responsibleUserId=reservation_data.responsibleUserId,
                status_webhook=False,  # Устанавливаем False по умолчанию
            )
            db.add(reservation)

            # Create room reservations
            # Create room reservations
            room_reservations = []
            for room_data in reservation_data.rooms:
                room_query = select(RoomReservation).where(
                    RoomReservation.roomReservationId == room_data.roomReservationId
                )
                room_result = await db.execute(room_query)
                existing_room = room_result.scalars().first()

                if existing_room:
                    logger.debug(
                        f"Комната {room_data.roomReservationId} уже существует"
                    )
                    # Обновляем существующую комнату
                    room_update_data = {
                        key: value
                        for key, value in room_data.dict().items()
                        if key != "roomReservationId" and value is not None
                    }

                    if (
                        room_update_data
                    ):  # Этот блок должен быть внутри if existing_room
                        await db.execute(
                            update(RoomReservation)
                            .where(
                                RoomReservation.roomReservationId
                                == room_data.roomReservationId
                            )
                            .values(**room_update_data)
                        )

                    # Добавляем данные существующей комнаты в результат
                    room_data_dict = {
                        "roomReservationId": existing_room.roomReservationId,
                        "roomId": existing_room.roomId,
                        "categoryId": existing_room.categoryId,
                        "arrival": existing_room.arrival,
                        "departure": existing_room.departure,
                        "guestName": existing_room.guestName,
                        "numberOfGuests": existing_room.numberOfGuests,
                        "rateId": existing_room.rateId,
                        "status": existing_room.status,
                        "currencyCode": existing_room.currencyCode,
                        "invoice": existing_room.invoice,
                        "paid": existing_room.paid,
                        "locked": existing_room.locked,
                        "detailed": existing_room.detailed,
                        "addOns": existing_room.addOns,
                        "guestExtraCharges": existing_room.guestExtraCharges,
                    }
                    room_reservations.append(room_data_dict)
                else:
                    # Создаем новую комнату
                    room_reservation = RoomReservation(
                        roomReservationId=room_data.roomReservationId,
                        reservationId=reservation_data.id,
                        roomId=room_data.roomId,
                        categoryId=room_data.categoryId,
                        arrival=room_data.arrival,
                        departure=room_data.departure,
                        guestName=room_data.guestName,
                        numberOfGuests=room_data.numberOfGuests,
                        rateId=room_data.rateId,
                        status=room_data.status,
                        currencyCode=room_data.currencyCode,
                        invoice=room_data.invoice,
                        paid=room_data.paid,
                        locked=room_data.locked,
                        detailed=room_data.detailed,
                        addOns=room_data.addOns,
                        guestExtraCharges=room_data.guestExtraCharges,
                    )
                    db.add(room_reservation)
                    room_reservations.append(
                        {
                            "roomReservationId": room_data.roomReservationId,
                            "roomId": room_data.roomId,
                            "categoryId": room_data.categoryId,
                            "arrival": room_data.arrival,
                            "departure": room_data.departure,
                            "guestName": room_data.guestName,
                            "numberOfGuests": room_data.numberOfGuests,
                            "rateId": room_data.rateId,
                            "status": room_data.status,
                            "currencyCode": room_data.currencyCode,
                            "invoice": room_data.invoice,
                            "paid": room_data.paid,
                            "locked": room_data.locked,
                            "detailed": room_data.detailed,
                            "addOns": room_data.addOns,
                            "guestExtraCharges": room_data.guestExtraCharges,
                        }
                    )

            # Важно: commit должен быть после цикла, а не внутри него
            logger.debug("Выполнение commit в базу данных")
            await db.commit()

            # Вместо загрузки объекта из базы, вернем созданные данные
            result = {
                "id": reservation_data.id,
                "organizationId": reservation_data.organizationId,
                "customer": {
                    "name": reservation_data.customer.name,
                    "email": reservation_data.customer.email,
                    "telephone": reservation_data.customer.telephone,
                    "remarks": reservation_data.customer.remarks,
                },
                "rooms": room_reservations,
                "status": reservation_data.status,
                "services": reservation_data.services,
                "bookedAt": reservation_data.bookedAt,
                "modifiedAt": reservation_data.modifiedAt,
                "source": reservation_data.source,
                "responsibleUserId": reservation_data.responsibleUserId,
            }

            logger.info(f"Created new reservation with ID: {reservation_data.id}")
            return result

        except Exception as e:
            await db.rollback()
            logger.error(f"Ошибка при создании бронирования: {str(e)}", exc_info=True)

            raise

    @staticmethod
    async def get_reservation(
        db: AsyncSession, reservation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a reservation by ID."""
        try:
            # Получаем данные бронирования
            query = select(Reservation).where(Reservation.id == reservation_id)
            result = await db.execute(query)
            reservation = result.scalars().first()

            if not reservation:
                logger.warning(f"Reservation with ID {reservation_id} not found")
                return None

            # Получаем данные клиента
            customer_query = select(Customer).where(
                Customer.id == reservation.customerId
            )
            customer_result = await db.execute(customer_query)
            customer = customer_result.scalars().first()

            # Получаем данные номеров
            rooms_query = select(RoomReservation).where(
                RoomReservation.reservationId == reservation_id
            )
            rooms_result = await db.execute(rooms_query)
            rooms = rooms_result.scalars().all()

            # Формируем ответ
            rooms_data = []
            for room in rooms:
                rooms_data.append(
                    {
                        "roomReservationId": room.roomReservationId,
                        "roomId": room.roomId,
                        "categoryId": room.categoryId,
                        "arrival": room.arrival,
                        "departure": room.departure,
                        "guestName": room.guestName,
                        "numberOfGuests": room.numberOfGuests,
                        "rateId": room.rateId,
                        "status": room.status,
                        "currencyCode": room.currencyCode,
                        "invoice": room.invoice,
                        "paid": room.paid,
                        "locked": room.locked,
                        "detailed": room.detailed,
                        "addOns": room.addOns,
                        "guestExtraCharges": room.guestExtraCharges,
                    }
                )

            reservation_data = {
                "id": reservation.id,
                "organizationId": reservation.organizationId,
                "customer": {
                    "name": customer.name,
                    "email": customer.email,
                    "telephone": customer.telephone,
                    "remarks": customer.remarks,
                },
                "rooms": rooms_data,
                "status": reservation.status,
                "services": reservation.services,
                "bookedAt": reservation.bookedAt,
                "modifiedAt": reservation.modifiedAt,
                "source": reservation.source,
                "responsibleUserId": reservation.responsibleUserId,
            }

            logger.info(f"Retrieved reservation with ID: {reservation_id}")
            return reservation_data

        except Exception as e:
            logger.error(f"Error retrieving reservation {reservation_id}: {str(e)}")
            raise

    @staticmethod
    async def get_reservations(
        db: AsyncSession,
        filters: Optional[ReservationFilter] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get all reservations with optional filters."""
        try:
            # Базовый запрос для бронирований
            query = select(Reservation)

            # Применяем фильтры, если они предоставлены
            if filters:
                if filters.id:
                    query = query.where(Reservation.id == filters.id)
                if filters.organizationId:
                    query = query.where(
                        Reservation.organizationId == filters.organizationId
                    )
                if filters.status:
                    query = query.where(Reservation.status == filters.status)
                if filters.source:
                    query = query.where(Reservation.source == filters.source)
                if filters.responsibleUserId:
                    query = query.where(
                        Reservation.responsibleUserId == filters.responsibleUserId
                    )
                if filters.bookedAt_from:
                    query = query.where(Reservation.bookedAt >= filters.bookedAt_from)
                if filters.bookedAt_to:
                    query = query.where(Reservation.bookedAt <= filters.bookedAt_to)

                # Фильтры для связанных моделей будем обрабатывать после получения базовых данных

            # Применяем пагинацию
            query = query.offset(skip).limit(limit)

            # Выполняем запрос
            result = await db.execute(query)
            reservations = result.scalars().all()

            # Обработка результатов
            reservation_list = []
            for reservation in reservations:
                # Получаем связанного клиента
                customer_query = select(Customer).where(
                    Customer.id == reservation.customerId
                )
                customer_result = await db.execute(customer_query)
                customer = customer_result.scalars().first()

                if not customer:
                    logger.warning(
                        f"Customer for reservation {reservation.id} not found"
                    )
                    continue

                # Получаем связанные номера
                rooms_query = select(RoomReservation).where(
                    RoomReservation.reservationId == reservation.id
                )
                rooms_result = await db.execute(rooms_query)
                rooms = rooms_result.scalars().all()

                # Проверяем фильтры, связанные с номерами
                skip_reservation = False
                if filters:
                    if (
                        filters.arrival_from
                        or filters.arrival_to
                        or filters.departure_from
                        or filters.departure_to
                    ):

                        room_matches = False
                        for room in rooms:
                            matches = True
                            if (
                                filters.arrival_from
                                and room.arrival < filters.arrival_from
                            ):
                                matches = False
                            if filters.arrival_to and room.arrival > filters.arrival_to:
                                matches = False
                            if (
                                filters.departure_from
                                and room.departure < filters.departure_from
                            ):
                                matches = False
                            if (
                                filters.departure_to
                                and room.departure > filters.departure_to
                            ):
                                matches = False

                            if matches:
                                room_matches = True
                                break

                        if not room_matches:
                            skip_reservation = True

                    # Проверяем фильтр по имени клиента
                    if (
                        filters.customer_name
                        and filters.customer_name.lower() not in customer.name.lower()
                    ):
                        skip_reservation = True

                if skip_reservation:
                    continue

                # Форматируем данные номеров
                rooms_data = []
                for room in rooms:
                    rooms_data.append(
                        {
                            "roomReservationId": room.roomReservationId,
                            "roomId": room.roomId,
                            "categoryId": room.categoryId,
                            "arrival": room.arrival,
                            "departure": room.departure,
                            "guestName": room.guestName,
                            "numberOfGuests": room.numberOfGuests,
                            "rateId": room.rateId,
                            "status": room.status,
                            "currencyCode": room.currencyCode,
                            "invoice": room.invoice,
                            "paid": room.paid,
                            "locked": room.locked,
                            "detailed": room.detailed,
                            "addOns": room.addOns,
                            "guestExtraCharges": room.guestExtraCharges,
                        }
                    )

                # Формируем данные бронирования
                reservation_data = {
                    "id": reservation.id,
                    "organizationId": reservation.organizationId,
                    "customer": {
                        "name": customer.name,
                        "email": customer.email,
                        "telephone": customer.telephone,
                        "remarks": customer.remarks,
                    },
                    "rooms": rooms_data,
                    "status": reservation.status,
                    "services": reservation.services,
                    "bookedAt": reservation.bookedAt,
                    "modifiedAt": reservation.modifiedAt,
                    "source": reservation.source,
                    "responsibleUserId": reservation.responsibleUserId,
                }

                reservation_list.append(reservation_data)

            logger.info(f"Retrieved {len(reservation_list)} reservations")
            return reservation_list

        except Exception as e:
            logger.error(f"Error retrieving reservations: {str(e)}")
            raise

    @staticmethod
    async def update_reservation(
        db: AsyncSession, reservation_id: str, reservation_data: ReservationUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update an existing reservation."""
        try:
            # Проверяем существование бронирования
            check_query = select(Reservation).where(Reservation.id == reservation_id)
            result = await db.execute(check_query)
            reservation = result.scalars().first()

            if not reservation:
                logger.warning(
                    f"Cannot update: Reservation with ID {reservation_id} not found"
                )
                return None

            # Получаем данные клиента
            customer_query = select(Customer).where(
                Customer.id == reservation.customerId
            )
            customer_result = await db.execute(customer_query)
            customer = customer_result.scalars().first()

            if not customer:
                logger.warning(
                    f"Cannot update: Customer for reservation {reservation_id} not found"
                )
                return None

            # Set current timestamp for modification
            current_time = int(time.time() * 1000)

            # Update reservation fields
            update_data = {"modifiedAt": current_time}

            if reservation_data.status is not None:
                update_data["status"] = reservation_data.status
            if reservation_data.services is not None:
                update_data["services"] = reservation_data.services
            if reservation_data.source is not None:
                update_data["source"] = reservation_data.source
            if reservation_data.responsibleUserId is not None:
                update_data["responsibleUserId"] = reservation_data.responsibleUserId

            # Update the reservation
            if update_data:
                await db.execute(
                    update(Reservation)
                    .where(Reservation.id == reservation_id)
                    .values(**update_data)
                )
            customer_updated = False  # Добавляем инициализацию переменной

            # Update customer if provided
            if reservation_data.customer:
                # ВАЖНОЕ ИЗМЕНЕНИЕ: преобразуем Pydantic модель в словарь перед обновлением
                customer_dict = reservation_data.customer.dict(exclude_unset=True)
                if customer_dict:
                    try:
                        await db.execute(
                            update(Customer)
                            .where(Customer.id == reservation.customerId)
                            .values(**customer_dict)
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при обновлении customer: {str(e)}")
                        # Альтернативное обновление по отдельным полям
                        if "name" in customer_dict:
                            await db.execute(
                                update(Customer)
                                .where(Customer.id == reservation.customerId)
                                .values(name=customer_dict["name"])
                            )
                        if "email" in customer_dict:
                            await db.execute(
                                update(Customer)
                                .where(Customer.id == reservation.customerId)
                                .values(email=customer_dict["email"])
                            )
                        if "telephone" in customer_dict:
                            await db.execute(
                                update(Customer)
                                .where(Customer.id == reservation.customerId)
                                .values(telephone=customer_dict["telephone"])
                            )
                        if "remarks" in customer_dict:
                            await db.execute(
                                update(Customer)
                                .where(Customer.id == reservation.customerId)
                                .values(remarks=customer_dict["remarks"])
                            )

            # Update room reservations if provided
            rooms_updated = False
            if reservation_data.rooms:
                # Get existing room reservations
                rooms_query = select(RoomReservation).where(
                    RoomReservation.reservationId == reservation_id
                )
                rooms_result = await db.execute(rooms_query)
                existing_rooms = {
                    room.roomReservationId: room
                    for room in rooms_result.scalars().all()
                }

                # Process each room in the update data
                for room_data in reservation_data.rooms:
                    room_id = room_data.roomReservationId

                    # If room exists, update it
                    if room_id in existing_rooms:
                        room_update_data = {
                            key: value
                            for key, value in room_data.dict().items()
                            if key != "roomReservationId" and value is not None
                        }

                        if room_update_data:
                            await db.execute(
                                update(RoomReservation)
                                .where(RoomReservation.roomReservationId == room_id)
                                .values(**room_update_data)
                            )
                            rooms_updated = True

            await db.commit()

            # Формируем обновленный ответ
            if customer_updated or update_data or rooms_updated:
                # Если были изменения, снова запрашиваем данные
                return await ReservationService.get_reservation(db, reservation_id)
            else:
                # Если не было изменений, возвращаем исходное бронирование
                return await ReservationService.get_reservation(db, reservation_id)

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating reservation {reservation_id}: {str(e)}")
            raise

    @staticmethod
    async def delete_reservation(db: AsyncSession, reservation_id: str) -> bool:
        """Delete a reservation."""
        try:
            # Check if reservation exists
            query = select(Reservation).where(Reservation.id == reservation_id)
            result = await db.execute(query)
            reservation = result.scalars().first()

            if not reservation:
                logger.warning(
                    f"Cannot delete: Reservation with ID {reservation_id} not found"
                )
                return False

            # Delete room reservations (could be handled by cascade, but being explicit)
            await db.execute(
                delete(RoomReservation).where(
                    RoomReservation.reservationId == reservation_id
                )
            )

            # Delete reservation
            await db.execute(
                delete(Reservation).where(Reservation.id == reservation_id)
            )

            # Note: Not deleting the customer as it might be associated with other reservations

            await db.commit()
            logger.info(f"Deleted reservation with ID: {reservation_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting reservation {reservation_id}: {str(e)}")
            raise
