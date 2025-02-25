from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactResponse
from configuration.logger_setup import logger
from sqlalchemy.future import select
from app.schemas.contact import ContactFilter, PaginatedResponse, ContactMini
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.sql import func
from app.models.telegram_message import TelegramMessage
from app.models.telegram_users import TelegramUser
from sqlalchemy import update
from sqlalchemy import update, select, or_, and_
from app.schemas.telegram import MessageQuerySchema, UserSchema, MessageSchema
from sqlalchemy.orm import joinedload


# from app.schemas.telegram_message import TelegramMessageCreate
from app.schemas.telegram import TelegramMessageSchema, MessageReadSchema


router = APIRouter()


@router.post("/contact", response_model=ContactResponse)
async def create_or_update_contact(
    contact: ContactCreate, db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Incoming contact data: {contact}")
    """
    Создать новый контакт или обновить существующий.
    """
    if contact.contact_id:
        # Проверяем, существует ли контакт
        existing_contact = await db.execute(
            select(Contact).where(Contact.id == contact.contact_id)
        )
        existing_contact = existing_contact.scalar_one_or_none()
        if not existing_contact:
            raise HTTPException(
                status_code=404,
                detail=f"Contact with ID {contact.contact_id} not found.",
            )

        # Обновляем существующий контакт
        existing_contact.username = contact.username
        existing_contact.contact_type = contact.contact_type
        existing_contact.contact_status = contact.contact_status
        existing_contact.manager = contact.manager
        existing_contact.userphone = contact.userphone
        existing_contact.useremail = contact.useremail
        existing_contact.usersite = contact.usersite
        existing_contact.comment = contact.comment
        try:
            await db.commit()
            await db.refresh(existing_contact)
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Ошибка обновления контакта: {str(e)}"
            )
        return existing_contact

    # Создаем новый контакт
    new_contact = Contact(
        username=contact.username,
        contact_type=contact.contact_type,
        contact_status=contact.contact_status,
        manager=contact.manager,
        userphone=contact.userphone,
        useremail=contact.useremail,
        usersite=contact.usersite,
        comment=contact.comment,
    )
    db.add(new_contact)
    try:
        await db.commit()
        await db.refresh(new_contact)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Ошибка создания контакта: {str(e)}"
        )
    return new_contact


@router.post("/contacts", response_model=PaginatedResponse)
async def post_filtered_contacts(
    filters: ContactFilter,
    mini: bool = Query(
        False, description="Возвращать только id и username", convert_underscores=False
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список контактов с фильтрацией, пагинацией и сортировкой.
    """
    try:
        # Основной запрос
        query = select(Contact)

        # Применение фильтров
        if filters.searchString and filters.searchString.strip():
            search_pattern = f"%{filters.searchString.strip()}%"
            query = query.where(
                (Contact.username.ilike(search_pattern))
                | (Contact.userphone.ilike(search_pattern))
                | (Contact.useremail.ilike(search_pattern))
            )

        if filters.statusFilter and filters.statusFilter.strip():
            query = query.where(Contact.contact_status == filters.statusFilter.strip())

        if filters.contactFilter and filters.contactFilter.strip():
            query = query.where(Contact.contact_type == filters.contactFilter.strip())

        if filters.start and filters.end:
            query = query.where(Contact.created_at.between(filters.start, filters.end))

        # Пагинация
        if filters.limit <= 0 or filters.page <= 0:
            raise HTTPException(status_code=400, detail="Invalid pagination parameters")

        offset = (filters.page - 1) * filters.limit
        query = query.offset(offset).limit(filters.limit)

        # Выполнение основного запроса
        results = await db.execute(query)
        contacts = results.scalars().all()

        # Подсчёт записей
        count_query = select(func.count(Contact.id)).where(*query._where_criteria)
        total_records = (await db.execute(count_query)).scalar()

        # Формирование ответа
        total_pages = (total_records + filters.limit - 1) // filters.limit
        response_content = {
            "data": jsonable_encoder(
                [ContactMini(id=c.id, username=c.username) for c in contacts]
                if mini
                else contacts
            ),
            "totalPages": total_pages,
            "currentPage": filters.page,
        }
        return response_content

    except Exception as e:
        logger.error(f"Ошибка при получении списка контактов: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/telegram/message")
async def post_telegram_message(
    message_data: TelegramMessageSchema, db: AsyncSession = Depends(get_db)
):
    # Проверка дубликатов message_id
    stmt = select(TelegramMessage).filter(
        TelegramMessage.message_id == message_data.message.message_id
    )
    result = await db.execute(stmt)
    existing_message = result.scalar_one_or_none()

    if existing_message:
        return {
            "message_id": existing_message.message_id,
            "status": "Message already exists",
        }

    # Проверка и создание отправителя
    stmt = select(TelegramUser).filter(
        TelegramUser.telegram_id == message_data.sender.telegram_id
    )
    result = await db.execute(stmt)
    sender = result.scalar_one_or_none()

    if not sender:
        sender = TelegramUser(
            name=message_data.sender.name,
            username=message_data.sender.username,
            telegram_id=message_data.sender.telegram_id,
            phone=message_data.sender.phone,
        )
        db.add(sender)
        await db.commit()
        await db.refresh(sender)

    # Проверка и создание получателя
    stmt = select(TelegramUser).filter(
        TelegramUser.telegram_id == message_data.recipient.telegram_id
    )
    result = await db.execute(stmt)
    recipient = result.scalar_one_or_none()

    if not recipient:
        recipient = TelegramUser(
            name=message_data.recipient.name,
            username=message_data.recipient.username,
            telegram_id=message_data.recipient.telegram_id,
            phone=message_data.recipient.phone,
        )
        db.add(recipient)
        await db.commit()
        await db.refresh(recipient)
    logger.info(f"Incoming message data: {message_data.dict()}")  # Добавить это

    # Перед созданием сообщения
    logger.info(f"Creating message with ID: {message_data.message.message_id}")

    # Создание сообщения
    new_message = TelegramMessage(
        message_id=message_data.message.message_id,
        sender_id=sender.id,
        recipient_id=recipient.id,
        message=message_data.message.text,
        is_reply=message_data.message.is_reply,
        reply_to=message_data.message.reply_to,
        is_read=message_data.message.read,
        direction=message_data.message.direction,  # Используем direction из сообщения
    )
    logger.info(f"Created message object with ID: {new_message.message_id}")
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return {"message_id": new_message.message_id, "status": "Message sent successfully"}


@router.post("/telegram/message/read")
async def update_message_read_status(
    read_data: MessageReadSchema, db: AsyncSession = Depends(get_db)
):
    """
    Обновляет статус сообщений на прочитанное.
    """
    try:
        logger.info(f"Получены данные для обновления: {read_data.dict()}")

        # Преобразуем telegram_id в внутренний id для отправителя
        sender_query = select(TelegramUser.id).where(
            TelegramUser.telegram_id == read_data.sender_id
        )
        recipient_query = select(TelegramUser.id).where(
            TelegramUser.telegram_id == read_data.recipient_id
        )

        sender_result = await db.execute(sender_query)
        sender_id = sender_result.scalar_one_or_none()

        recipient_result = await db.execute(recipient_query)
        recipient_id = recipient_result.scalar_one_or_none()

        # Проверяем, что отправитель и получатель существуют
        if sender_id is None or recipient_id is None:
            raise HTTPException(
                status_code=404,
                detail="Sender or recipient not found in the database",
            )

        # Логируем преобразованные ID
        logger.info(
            f"Преобразованные ID: sender_id={sender_id}, recipient_id={recipient_id}"
        )

        # Добавьте этот код перед update для диагностики
        check_query = (
            select(TelegramMessage)
            .where(
                or_(
                    and_(
                        TelegramMessage.sender_id == sender_id,
                        TelegramMessage.recipient_id == recipient_id,
                    ),
                    and_(
                        TelegramMessage.sender_id == recipient_id,
                        TelegramMessage.recipient_id == sender_id,
                    ),
                )
            )
            .order_by(TelegramMessage.message_id)
        )

        messages = await db.execute(check_query)
        messages = messages.scalars().all()

        logger.info(f"Total messages in conversation: {len(messages)}")
        logger.info("Message IDs distribution:")
        id_counts = {}
        for msg in messages:
            if msg.message_id in id_counts:
                id_counts[msg.message_id] += 1
            else:
                id_counts[msg.message_id] = 1

        for msg_id, count in sorted(id_counts.items()):
            if count > 1 or msg_id == 0:
                logger.info(f"Message ID {msg_id}: {count} occurrences")

        # Обновляем статус сообщений по message_id
        stmt = (
            update(TelegramMessage)
            .where(
                or_(
                    and_(
                        TelegramMessage.sender_id == sender_id,
                        TelegramMessage.recipient_id == recipient_id,
                    ),
                    and_(
                        TelegramMessage.sender_id == recipient_id,
                        TelegramMessage.recipient_id == sender_id,
                    ),
                ),
                TelegramMessage.message_id <= read_data.max_id,
                TelegramMessage.message_id > 0,  # Добавить эту проверку
            )
            .values(is_read=True)
        )
        result = await db.execute(stmt)
        logger.info(f"Количество обновленных сообщений: {result.rowcount}")

        await db.commit()

        return {"status": "Messages marked as read", "max_id": read_data.max_id}

    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса сообщений: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update message read status"
        )


@router.post("/telegram/chat", response_model=list[TelegramMessageSchema])
async def get_chat_messages(
    query_params: MessageQuerySchema, db: AsyncSession = Depends(get_db)
):
    """
    Получить сообщения между двумя пользователями с пагинацией.

    :param query_params: Параметры запроса (telegram_id отправителя, telegram_id получателя, лимит, смещение)
    :param db: Асинхронная сессия базы данных
    :return: Список сообщений с полными данными
    """
    try:
        logger.info(f"Запрос на получение сообщений: {query_params.model_dump()}")

        # Получаем пользователей по их telegram_id
        sender_query = select(TelegramUser).where(
            TelegramUser.telegram_id == query_params.sender_id
        )
        recipient_query = select(TelegramUser).where(
            TelegramUser.telegram_id == query_params.recipient_id
        )

        sender_result = await db.execute(sender_query)
        sender = sender_result.scalar_one_or_none()

        recipient_result = await db.execute(recipient_query)
        recipient = recipient_result.scalar_one_or_none()

        if sender is None or recipient is None:
            logger.warning(
                f"Пользователь не найден: telegram_id_sender={query_params.sender_id}, telegram_id_recipient={query_params.recipient_id}"
            )
            raise HTTPException(
                status_code=404,
                detail="Sender or recipient not found in the database",
            )

        # Запрос на получение сообщений между двумя пользователями
        # Включаем сообщения, отправленные в обоих направлениях
        query = (
            select(TelegramMessage)
            .options(
                joinedload(TelegramMessage.sender),
                joinedload(TelegramMessage.recipient),
            )
            .where(
                or_(
                    and_(
                        TelegramMessage.sender_id == sender.id,
                        TelegramMessage.recipient_id == recipient.id,
                    ),
                    and_(
                        TelegramMessage.sender_id == recipient.id,
                        TelegramMessage.recipient_id == sender.id,
                    ),
                )
            )
            .order_by(
                TelegramMessage.created_at.desc()
            )  # Сортировка по времени создания (новые сначала)
            .offset(query_params.offset)
            .limit(query_params.limit)
        )

        result = await db.execute(query)
        messages = result.scalars().all()

        if not messages:
            logger.info("Сообщения между указанными пользователями не найдены.")
            return []

        # Преобразуем сообщения в формат ответа
        serialized_messages = [
            TelegramMessageSchema(
                sender=UserSchema(
                    name=message.sender.name,
                    username=message.sender.username,
                    telegram_id=message.sender.telegram_id,
                    phone=message.sender.phone,
                ),
                recipient=UserSchema(
                    name=message.recipient.name,
                    username=message.recipient.username,
                    telegram_id=message.recipient.telegram_id,
                    phone=message.recipient.phone,
                ),
                message=MessageSchema(
                    message_id=message.message_id,
                    text=message.message,
                    is_reply=message.is_reply,
                    reply_to=message.reply_to,
                    read=message.is_read,
                    direction=message.direction,
                ),
            )
            for message in messages
        ]

        logger.info(
            f"Найдено {len(serialized_messages)} сообщений между пользователями."
        )
        return serialized_messages

    except Exception as e:
        logger.error(f"Ошибка при получении сообщений чата: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка при получении сообщений чата: {e}"
        )
