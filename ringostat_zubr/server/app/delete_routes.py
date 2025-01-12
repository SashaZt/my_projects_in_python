import json
from datetime import datetime  # Добавлен импорт для работы с датой и временем
from pydantic import BaseModel, validator
from typing import List
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException
from database import DatabaseInitializer, wait_for_db

router = APIRouter()

async def get_db():
    db_initializer = DatabaseInitializer()
    await wait_for_db()  # Проверяем доступность базы данных
    await db_initializer.create_database()
    await db_initializer.create_pool()  # Создаём пул соединений
    await db_initializer.init_db()
    return db_initializer

# Модель для входных данных
class DeleteRecord(BaseModel):
    call_date: str
    caller_number: str
    employee_ext_number: str
    employee: str

    # Валидатор для преобразования call_date
    @validator("call_date", pre=True)
    def format_call_date(cls, value):
        try:
            # Преобразуем формат из YYYY-MM-DD_HH-MM-SS в YYYY-MM-DD HH:MM:SS
            return datetime.strptime(value, "%Y-%m-%d_%H-%M-%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(f"Invalid call_date format: {value}. Expected YYYY-MM-DD_HH-MM-SS") from e

@router.delete("/delete_records")
async def delete_records(records: List[DeleteRecord], db=Depends(get_db)):
    """
    Удаляет записи из базы данных по критериям с последовательной проверкой.

    :param records: Список записей для удаления.
    :param db: Экземпляр базы данных.
    :return: Статус удаления.
    """
    if not records:
        raise HTTPException(status_code=400, detail="No records provided for deletion")

    try:
        async with db.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                deleted_count = 0
                for record in records:
                    # Проверяем наличие записи с указанными критериями
                    await cursor.execute(
                        """
                        SELECT * FROM calls_zubr
                        WHERE call_date = %s AND
                              caller_number = %s AND
                              employee_ext_number = %s AND
                              employee = %s
                        """,
                        (
                            record.call_date,
                            record.caller_number,
                            record.employee_ext_number,
                            record.employee,
                        ),
                    )
                    result = await cursor.fetchone()

                    if result:
                        # Удаляем запись, если она найдена
                        await cursor.execute(
                            """
                            DELETE FROM calls_zubr
                            WHERE call_date = %s AND
                                  caller_number = %s AND
                                  employee_ext_number = %s AND
                                  employee = %s
                            """,
                            (
                                record.call_date,
                                record.caller_number,
                                record.employee_ext_number,
                                record.employee,
                            ),
                        )
                        deleted_count += 1

                # Фиксируем изменения
                await connection.commit()

        if deleted_count > 0:
            logger.info(f"Удалено {deleted_count} записей из базы данных.")
            return {"status": "success", "message": f"{deleted_count} records deleted"}
        else:
            logger.warning("Ни одна запись не была найдена для удаления.")
            return {"status": "warning", "message": "No records matched for deletion"}

    except Exception as e:
        logger.error(f"Ошибка при удалении записей из базы данных: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to delete records from the database"
        )