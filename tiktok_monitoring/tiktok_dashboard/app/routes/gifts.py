# app/routes/gifts.py
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional

from database import db
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def list_gifts(request: Request):
    """Страница со списком подарков"""
    return templates.TemplateResponse("gifts.html", {"request": request})


@router.get("/api")
async def get_gifts(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=10, le=100),
    cluster: Optional[str] = None,
    streamer_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """API для получения подарков с фильтрацией и пагинацией"""
    # Базовый запрос
    query = """
    SELECT g.id, g.event_time, g.unique_id, g.user_id, g.gift_name, g.gift_count, 
        g.diamond_count, g.receiver_unique_id, ttu.name as streamer_name, 
        c.name as cluster_name
    FROM gifts g
    JOIN streamers s ON g.streamer_id = s.id
    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
    JOIN clusters c ON s.cluster_id = c.id
    WHERE 1=1
    """
    params = []

    # Добавляем фильтры, если они указаны
    if cluster:
        query += f" AND c.name = ${len(params) + 1}"
        params.append(cluster)

    if streamer_id:
        query += f" AND s.id = ${len(params) + 1}"
        params.append(streamer_id)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query += f" AND g.event_time >= ${len(params) + 1}"
            params.append(date_from_obj)
        except ValueError:
            pass  # Игнорируем некорректный формат даты

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(
                days=1
            )  # До конца дня
            query += f" AND g.event_time < ${len(params) + 1}"
            params.append(date_to_obj)
        except ValueError:
            pass  # Игнорируем некорректный формат даты

    # Добавляем сортировку и пагинацию
    query += (
        " ORDER BY g.event_time DESC LIMIT $"
        + str(len(params) + 1)
        + " OFFSET $"
        + str(len(params) + 2)
    )
    params.extend([limit, (page - 1) * limit])

    # Выполняем запрос
    gifts = await db.fetch(query, *params)

    # Преобразуем результаты
    result = []
    for gift in gifts:
        dollar_amount = gift["diamond_count"] * gift["gift_count"] / 200
        result.append(
            {
                "id": gift["id"],
                "event_time": gift["event_time"].isoformat(),
                "unique_id": gift["unique_id"],
                "user_id": gift["user_id"],
                "gift_name": gift["gift_name"],
                "gift_count": gift["gift_count"],
                "diamond_count": gift["diamond_count"],
                "dollar_amount": round(dollar_amount, 2),
                "receiver_unique_id": gift["receiver_unique_id"],
                "streamer_name": gift["streamer_name"],
                "cluster_name": gift["cluster_name"],
            }
        )

    # Получаем общее количество подарков для пагинации
    count_query = """
    SELECT COUNT(*) FROM gifts g
    JOIN streamers s ON g.streamer_id = s.id
    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
    JOIN clusters c ON s.cluster_id = c.id
    WHERE 1=1
    """

    # Добавляем те же фильтры
    count_params = []
    if cluster:
        count_query += f" AND c.name = ${len(count_params) + 1}"
        count_params.append(cluster)

    if streamer_id:
        count_query += f" AND s.id = ${len(count_params) + 1}"
        count_params.append(streamer_id)

    if date_from:
        try:
            count_query += f" AND g.event_time >= ${len(count_params) + 1}"
            count_params.append(date_from_obj)
        except UnboundLocalError:
            pass

    if date_to:
        try:
            count_query += f" AND g.event_time < ${len(count_params) + 1}"
            count_params.append(date_to_obj)
        except UnboundLocalError:
            pass

    total_count = await db.fetchval(count_query, *count_params)
    total_pages = (total_count + limit - 1) // limit  # Округление вверх

    return {
        "gifts": result,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


@router.get("/export")
async def export_gifts(
    cluster: Optional[str] = None,
    streamer_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    format: str = "csv",
):
    """Экспорт подарков в CSV или Excel"""
    # Базовый запрос
    query = """
    SELECT g.id, g.event_time, g.unique_id, g.user_id, g.gift_name, g.gift_count, 
        g.diamond_count, g.receiver_unique_id, ttu.name as streamer_name, 
        c.name as cluster_name
    FROM gifts g
    JOIN streamers s ON g.streamer_id = s.id
    JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
    JOIN clusters c ON s.cluster_id = c.id
    WHERE 1=1
    """
    params = []

    # Добавляем фильтры, если они указаны
    if cluster:
        query += f" AND c.name = ${len(params) + 1}"
        params.append(cluster)

    if streamer_id:
        query += f" AND s.id = ${len(params) + 1}"
        params.append(streamer_id)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query += f" AND g.event_time >= ${len(params) + 1}"
            params.append(date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query += f" AND g.event_time < ${len(params) + 1}"
            params.append(date_to_obj)
        except ValueError:
            pass

    # Сортировка
    query += " ORDER BY g.event_time DESC"

    # Выполняем запрос
    gifts = await db.fetch(query, *params)

    # Экспорт в CSV
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Заголовки
        writer.writerow(
            [
                "ID",
                "Дата",
                "Донатер",
                "UserID донатера",
                "Подарок",
                "Количество",
                "Диаманты",
                "Сумма ($)",
                "Стример",
                "Кластер",
            ]
        )

        # Данные
        for gift in gifts:
            dollar_amount = gift["diamond_count"] * gift["gift_count"] / 200
            writer.writerow(
                [
                    gift["id"],
                    gift["event_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    gift["unique_id"],
                    gift["user_id"],
                    gift["gift_name"],
                    gift["gift_count"],
                    gift["diamond_count"],
                    f"{dollar_amount:.2f}",
                    gift["streamer_name"],
                    gift["cluster_name"],
                ]
            )

        output.seek(0)

        # Формируем имя файла
        filename = f"gifts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Возвращаем файл
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"},
        )
    else:
        # Поддержка других форматов можно добавить позже
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат экспорта")
