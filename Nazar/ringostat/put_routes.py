
from configuration.logger_setup import logger
from fastapi.responses import JSONResponse
from dependencies import get_db
from database import DatabaseInitializer  # Импорт класса для работы с базой данных
from fastapi import APIRouter, HTTPException, Depends, Query

router = APIRouter()
router = APIRouter()

async def get_db():
    db_initializer = DatabaseInitializer()
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    return db_initializer
@router.put("/contacts/{itemId}/status")
async def update_contact_status(itemId: int, status: str = Query(...), db=Depends(get_db)):
    try:
        async with db.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                # Обновляем статус контакта по его ID
                update_query = "UPDATE contacts SET contact_status = %s WHERE id = %s"
                await cursor.execute(update_query, (status, itemId))
                await connection.commit()

        return JSONResponse(status_code=200, content={"status": "success", "itemId": itemId, "newStatus": status})

    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса контакта: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")