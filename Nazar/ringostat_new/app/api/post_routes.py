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

# from app.schemas.telegram_message import TelegramMessageCreate
from app.schemas.telegram import TelegramMessageSchema


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
    # Проверка и, если нужно, создание отправителя
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
        try:
            await db.commit()
        except IntegrityError:
            # Если произошла ошибка целостности данных, откатываем и продолжаем без создания пользователя
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Failed to create sender due to data integrity error",
            )
        else:
            await db.refresh(sender)

    # Аналогично для получателя
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
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Failed to create recipient due to data integrity error",
            )
        else:
            await db.refresh(recipient)

    # Создание и добавление сообщения
    new_message = TelegramMessage(
        sender_id=sender.id,
        recipient_id=recipient.id,
        message=message_data.message.text,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return {"message_id": new_message.id, "status": "Message sent successfully"}


# @router.post("/telegram/message")
# async def save_telegram_message(
#     message: TelegramMessageCreate, db: AsyncSession = Depends(get_db)
# ):
#     """
#     Сохраняет сообщение Telegram в базу данных, создавая или обновляя записи отправителя и получателя.

#     :param message: Входные данные сообщения.
#     :param db: Асинхронная сессия базы данных.
#     :return: Сохранённое сообщение в формате JSON.
#     """
#     logger.info(f"Получены данные для сохранения: {message}")

#     try:
#         # Проверяем существование отправителя
#         sender_query = await db.execute(
#             select(TelegramUser).where(
#                 TelegramUser.telegram_id == message.sender.telegram_id
#             )
#         )
#         sender = sender_query.scalar_one_or_none()

#         if not sender:
#             sender = TelegramUser(
#                 name=message.sender.name,
#                 username=message.sender.username,
#                 telegram_id=message.sender.telegram_id,
#                 phone=message.sender.phone,
#             )
#             db.add(sender)
#             logger.info(f"Создан новый отправитель: {sender}")

#         # Проверяем существование получателя
#         recipient_query = await db.execute(
#             select(TelegramUser).where(
#                 TelegramUser.telegram_id == message.recipient.telegram_id
#             )
#         )
#         recipient = recipient_query.scalar_one_or_none()

#         if not recipient:
#             recipient = TelegramUser(
#                 name=message.recipient.name,
#                 username=message.recipient.username,
#                 telegram_id=message.recipient.telegram_id,
#                 phone=message.recipient.phone,
#             )
#             db.add(recipient)
#             logger.info(f"Создан новый получатель: {recipient}")

#         await db.flush()  # Обновляем объекты, чтобы получить их ID

#         # Создаём сообщение
#         new_message = TelegramMessage(
#             sender_id=sender.id,
#             recipient_id=recipient.id,
#             message=message.message.text,
#         )
#         db.add(new_message)

#         await db.commit()
#         await db.refresh(new_message)
#         logger.info("Сообщение успешно сохранено в базу данных.")
#         return new_message


#     except Exception as e:
#         await db.rollback()
#         logger.error(f"Ошибка при сохранении сообщения: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Ошибка при сохранении сообщения: {str(e)}"
#         )
