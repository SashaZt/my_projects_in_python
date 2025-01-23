from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactResponse
from configuration.logger_setup import logger
from sqlalchemy.future import select

router = APIRouter()


from sqlalchemy.future import select


@router.post("/contacts", response_model=ContactResponse)
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
