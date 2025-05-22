# app/routes/dashboard.py
import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from services.statistics import get_dashboard_statistics

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница дашборда"""
    # Используем шаблоны из контекста приложения
    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/api/statistics")
async def get_statistics():
    """API-эндпоинт для получения статистики"""
    return await get_dashboard_statistics()


@router.get("/events")
async def events(request: Request):
    """SSE эндпоинт для получения обновлений в реальном времени"""

    async def event_generator():
        while True:
            # Проверяем, не закрыл ли клиент соединение
            if await request.is_disconnected():
                break

            # Получаем актуальные данные
            data = await get_dashboard_statistics()

            # Отправляем данные в формате SSE
            yield f"data: {json.dumps(data)}\n\n"

            # Пауза между обновлениями
            await asyncio.sleep(3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
