from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.transfer import Transfer as TransferModel  # SQLAlchemy‑модель
from app.schemas.transfer import TransferCreate  # Pydantic‑схема для создания
from app.core.logger import logger


async def get_transfer(db: AsyncSession, transfer_id: int) -> TransferModel:
    """
    Получить запись Transfer по её id.
    """
    logger.debug(f"Начат поиск записи Transfer с id={transfer_id}")
    result = await db.execute(
        select(TransferModel).where(TransferModel.id == transfer_id)
    )
    transfer = result.scalars().first()
    if transfer:
        logger.info(f"Запись Transfer с id={transfer_id} успешно найдена")
    else:
        logger.warning(f"Запись Transfer с id={transfer_id} не найдена")
    return transfer


async def get_transfers(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    Получить список записей Transfer с поддержкой пагинации.
    """
    logger.debug(
        f"Получение списка записей Transfer с параметрами: skip={skip}, limit={limit}"
    )
    result = await db.execute(select(TransferModel).offset(skip).limit(limit))
    transfers = result.scalars().all()
    logger.info(f"Получено {len(transfers)} записей Transfer")
    return transfers


async def create_transfer(db: AsyncSession, transfer: TransferCreate) -> TransferModel:
    """
    Создать новую запись Transfer.
    """
    logger.debug(f"Создание новой записи Transfer с данными: {transfer.dict()}")
    db_transfer = TransferModel(**transfer.dict())
    db.add(db_transfer)
    await db.commit()
    await db.refresh(db_transfer)
    logger.info(f"Новая запись Transfer успешно создана с id={db_transfer.id}")
    return db_transfer


async def update_transfer(
    db: AsyncSession, transfer_id: int, transfer_data: TransferCreate
) -> TransferModel:
    """
    Обновить существующую запись Transfer.
    """
    logger.debug(f"Начато обновление записи Transfer с id={transfer_id}")
    db_transfer = await get_transfer(db, transfer_id)
    if not db_transfer:
        logger.warning(
            f"Обновление не выполнено: запись Transfer с id={transfer_id} не найдена"
        )
        return None
    for key, value in transfer_data.dict(exclude_unset=True).items():
        setattr(db_transfer, key, value)
        logger.debug(f"Поле '{key}' обновлено на значение '{value}'")
    db.add(db_transfer)
    await db.commit()
    await db.refresh(db_transfer)
    logger.info(f"Запись Transfer с id={transfer_id} успешно обновлена")
    return db_transfer


async def delete_transfer(db: AsyncSession, transfer_id: int) -> bool:
    """
    Удалить запись Transfer по id.
    """
    logger.debug(f"Попытка удаления записи Transfer с id={transfer_id}")
    db_transfer = await get_transfer(db, transfer_id)
    if not db_transfer:
        logger.warning(
            f"Удаление не выполнено: запись Transfer с id={transfer_id} не найдена"
        )
        return False
    await db.delete(db_transfer)
    await db.commit()
    logger.info(f"Запись Transfer с id={transfer_id} успешно удалена")
    return True
