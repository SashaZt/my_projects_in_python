import json
import os
from datetime import datetime

from config import WEBHOOK_DATA_DIR
from config.logger import logger
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(title="TikTok Alerts Webhook")

# Создаем директорию для webhook-данных, если она не существует
os.makedirs(WEBHOOK_DATA_DIR, exist_ok=True)


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Эндпоинт для получения webhook-уведомлений от TikTok Alerts API"""
    try:
        # Получаем данные из запроса
        data = await request.json()

        # Формируем имя файла с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{WEBHOOK_DATA_DIR}/tiktok_webhook_{timestamp}.json"

        # Записываем данные в файл
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logger.info(f"Webhook данные сохранены в файл: {filename}")

        # Выводим полученные данные в консоль для отладки
        logger.info(
            f"Получены webhook-данные: {json.dumps(data, indent=2, ensure_ascii=False)}"
        )

        # Возвращаем успешный ответ
        return {
            "status": "success",
            "message": "Webhook данные успешно получены и сохранены",
        }

    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка при обработке webhook: {str(e)}"
        )


# Добавим дополнительный эндпоинт для проверки работоспособности сервера
@app.get("/")
def read_root():
    return {"status": "active", "message": "TikTok Alerts Webhook сервер активен"}
