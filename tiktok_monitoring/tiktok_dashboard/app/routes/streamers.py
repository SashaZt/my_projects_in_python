# /app/routes/str
from typing import Optional

from database import db
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class StreamerCreate(BaseModel):
    name: str
    cluster_id: int
    check_online: int = 30
    status: str = "Запущен"


class StreamerUpdate(BaseModel):
    cluster_id: Optional[int] = None
    check_online: Optional[int] = None
    status: Optional[str] = None


# @router.get("/", response_class=HTMLResponse)
# async def list_streamers(request: Request):
#     """Список стримеров"""
#     streamers = await db.fetch(
#         """
#         SELECT s.id, ttu.name, s.room_id, c.name as cluster_name,
#                s.status, s.check_online, s.last_activity
#         FROM streamers s
#         JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
#         LEFT JOIN clusters c ON s.cluster_id = c.id
#         ORDER BY ttu.name
#         """
#     )

#     total_streamers = len(streamers)
#     active_streamers = sum(1 for s in streamers if s["status"] == "Запущен")


#     return templates.TemplateResponse(
#         "streamers.html",
#         {
#             "request": request,
#             "streamers": streamers,
#             "total_streamers": total_streamers,
#             "active_streamers": active_streamers,
#         },
#     )
@router.get("/", response_class=HTMLResponse)
async def list_streamers(request: Request):
    """Список стримеров"""
    streamers = await db.fetch(
        """
        SELECT s.id, ttu.name, ttu.user_id, s.room_id, c.name as cluster_name, 
               s.status, s.check_online, s.last_activity
        FROM streamers s
        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
        LEFT JOIN clusters c ON s.cluster_id = c.id
        ORDER BY ttu.name
        """
    )

    total_streamers = len(streamers)
    active_streamers = sum(1 for s in streamers if s["status"] == "Запущен")

    return templates.TemplateResponse(
        "streamers.html",
        {
            "request": request,
            "streamers": streamers,
            "total_streamers": total_streamers,
            "active_streamers": active_streamers,
        },
    )


@router.get("/add", response_class=HTMLResponse)
async def add_streamer_form(request: Request):
    """Форма добавления стримера"""
    clusters = await db.fetch("SELECT id, name FROM clusters ORDER BY name")

    return templates.TemplateResponse(
        "streamer_add.html", {"request": request, "clusters": clusters}
    )


# @router.post("/add")
# async def add_streamer(
#     name: str = Form(...), cluster_id: int = Form(...), check_online: int = Form(30)
# ):
#     """Обработка формы добавления стримера"""
#     # Проверяем формат имени
#     formatted_name = name if name.startswith("@") else f"@{name}"

#     async with db.pool.acquire() as conn:
#         async with conn.transaction():
#             # Сначала проверяем, существует ли пользователь TikTok с таким именем
#             existing_user = await conn.fetchrow(
#                 "SELECT id FROM tik_tok_users WHERE name = $1", formatted_name
#             )

#             if existing_user:
#                 user_id = existing_user["id"]
#                 # Проверяем, не привязан ли уже этот пользователь к стримеру
#                 existing_streamer = await conn.fetchval(
#                     "SELECT id FROM streamers WHERE tik_tok_user_id = $1", user_id
#                 )
#                 if existing_streamer:
#                     raise HTTPException(
#                         status_code=400, detail="Стример с таким именем уже существует"
#                     )
#             else:
#                 # Создаем нового пользователя TikTok
#                 user_id = await conn.fetchval(
#                     """
#                     INSERT INTO tik_tok_users (name)
#                     VALUES ($1)
#                     RETURNING id
#                     """,
#                     formatted_name,
#                 )

#             # Создаем запись о стримере
#             await conn.execute(
#                 """
#                 INSERT INTO streamers (tik_tok_user_id, cluster_id, status, check_online)
#                 VALUES ($1, $2, $3, $4)
#                 """,
#                 user_id,
#                 cluster_id,
#                 "Запущен",
#                 check_online,
#             )


#     return RedirectResponse(url="/streamers", status_code=303)
@router.post("/add")
async def add_streamer(
    name: str = Form(...),
    user_id: Optional[str] = Form(None),
    cluster_id: int = Form(...),
    check_online: int = Form(30),
):
    """Обработка формы добавления стримера"""
    # Проверяем формат имени
    formatted_name = name if name.startswith("@") else f"@{name}"

    async with db.pool.acquire() as conn:
        async with conn.transaction():
            # Сначала проверяем, существует ли пользователь TikTok с таким именем
            existing_user = await conn.fetchrow(
                "SELECT id FROM tik_tok_users WHERE name = $1", formatted_name
            )

            if existing_user:
                user_tiktok_id = existing_user["id"]
                # Обновляем user_id, если он предоставлен
                if user_id:
                    await conn.execute(
                        "UPDATE tik_tok_users SET user_id = $1, updated_at = NOW() WHERE id = $2",
                        user_id,
                        user_tiktok_id,
                    )

                # Проверяем, не привязан ли уже этот пользователь к стримеру
                existing_streamer = await conn.fetchval(
                    "SELECT id FROM streamers WHERE tik_tok_user_id = $1",
                    user_tiktok_id,
                )
                if existing_streamer:
                    raise HTTPException(
                        status_code=400, detail="Стример с таким именем уже существует"
                    )
            else:
                # Создаем нового пользователя TikTok с указанным user_id (если предоставлен)
                user_tiktok_id = await conn.fetchval(
                    """
                    INSERT INTO tik_tok_users (name, user_id, created_at, updated_at) 
                    VALUES ($1, $2, NOW(), NOW())
                    RETURNING id
                    """,
                    formatted_name,
                    user_id,
                )

            # Конвертируем user_id в room_id, если возможно
            room_id = None
            if user_id and user_id.isdigit():
                try:
                    room_id = int(user_id)
                except ValueError:
                    room_id = None

            # Создаем запись о стримере
            await conn.execute(
                """
                INSERT INTO streamers (tik_tok_user_id, cluster_id, status, check_online, room_id) 
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_tiktok_id,
                cluster_id,
                "Запущен",
                check_online,
                room_id,
            )

    return RedirectResponse(url="/streamers", status_code=303)


@router.get("/edit/{streamer_id}", response_class=HTMLResponse)
async def edit_streamer_form(request: Request, streamer_id: int):
    """Форма редактирования стримера"""
    streamer = await db.fetchrow(
        """
        SELECT s.id, ttu.name, s.cluster_id, s.status, s.check_online, s.room_id
        FROM streamers s
        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
        WHERE s.id = $1
        """,
        streamer_id,
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    clusters = await db.fetch("SELECT id, name FROM clusters ORDER BY name")

    return templates.TemplateResponse(
        "streamer_edit.html",
        {"request": request, "streamer": streamer, "clusters": clusters},
    )


@router.post("/edit/{streamer_id}")
async def edit_streamer(
    streamer_id: int,
    cluster_id: int = Form(...),
    check_online: int = Form(30),
    status: str = Form("Запущен"),
):
    """Обработка формы редактирования стримера"""
    # Проверяем, существует ли стример
    streamer = await db.fetchrow(
        "SELECT id, status FROM streamers WHERE id = $1", streamer_id
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    # Обновляем запись о стримере
    await db.execute(
        """
        UPDATE streamers 
        SET cluster_id = $1, check_online = $2, status = $3
        WHERE id = $4
        """,
        cluster_id,
        check_online,
        status,
        streamer_id,
    )

    # Если изменился статус, обновляем мониторинг
    if streamer["status"] != status:
        if status == "Запущен":
            # Запускаем мониторинг
            # await start_monitoring(streamer_id)
            pass
        else:
            # Останавливаем мониторинг
            # await stop_monitoring(streamer_id)
            pass

    return RedirectResponse(url="/streamers", status_code=303)


@router.post("/toggle/{streamer_id}")
async def toggle_streamer(streamer_id: int):
    """Переключение статуса стримера (запущен/остановлен)"""
    # Получаем текущий статус и имя стримера через JOIN
    streamer = await db.fetchrow(
        """
        SELECT s.id, ttu.name, s.status 
        FROM streamers s
        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
        WHERE s.id = $1
        """,
        streamer_id,
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    # Меняем статус на противоположный
    new_status = "Остановлен" if streamer["status"] == "Запущен" else "Запущен"

    # Обновляем статус в базе
    await db.execute(
        "UPDATE streamers SET status = $1 WHERE id = $2", new_status, streamer_id
    )

    # Обновляем мониторинг
    if new_status == "Запущен":
        # Запускаем мониторинг
        # await start_monitoring(streamer['name'])
        pass
    else:
        # Останавливаем мониторинг
        # await stop_monitoring(streamer['name'])
        pass

    return {"status": "success", "new_status": new_status}


@router.delete("/{streamer_id}")
async def delete_streamer(streamer_id: int):
    """Удаление стримера"""
    # Проверяем, существует ли стример
    streamer = await db.fetchrow(
        """
        SELECT s.id, ttu.name, s.status 
        FROM streamers s
        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
        WHERE s.id = $1
        """,
        streamer_id,
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    # Если стример запущен, останавливаем мониторинг
    if streamer["status"] == "Запущен":
        # await stop_monitoring(streamer['name'])
        pass

    # Удаляем стримера из базы
    await db.execute("DELETE FROM streamers WHERE id = $1", streamer_id)

    return {"status": "success"}


@router.get("/profile/{streamer_id}", response_class=HTMLResponse)
async def streamer_profile(request: Request, streamer_id: int):
    """Профиль стримера"""
    # Получаем данные о стримере
    streamer = await db.fetchrow(
        """
        SELECT s.id, ttu.name, ttu.user_id, s.room_id, c.name as cluster_name, 
               s.status, s.check_online, s.last_activity
        FROM streamers s
        JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
        LEFT JOIN clusters c ON s.cluster_id = c.id
        WHERE s.id = $1
        """,
        streamer_id,
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    return templates.TemplateResponse(
        "streamer_profile.html", {"request": request, "streamer": streamer}
    )


# Добавьте API-маршруты для получения данных


@router.get("/api/profile/{streamer_id}/donations")
async def get_streamer_donations(
    streamer_id: int, period: str = Query("all", enum=["all", "month", "week", "day"])
):
    """API для получения донатов стримера"""
    # Получаем информацию о стримере
    streamer = await db.fetchrow(
        "SELECT id, tik_tok_user_id FROM streamers WHERE id = $1", streamer_id
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    # Подготавливаем запрос на основе выбранного периода
    query = """
    SELECT g.id, g.event_time, g.unique_id, g.gift_name, g.gift_count, 
           g.diamond_count, g.total_diamonds
    FROM gifts g
    WHERE g.streamer_id = $1
    """

    params = [streamer_id]

    if period == "month":
        # За текущий месяц
        query += (
            " AND DATE_TRUNC('month', g.event_time) = DATE_TRUNC('month', CURRENT_DATE)"
        )
    elif period == "week":
        # За текущую неделю
        query += (
            " AND DATE_TRUNC('week', g.event_time) = DATE_TRUNC('week', CURRENT_DATE)"
        )
    elif period == "day":
        # За сегодня
        query += " AND DATE_TRUNC('day', g.event_time) = CURRENT_DATE"

    query += " ORDER BY g.event_time DESC LIMIT 1000"

    # Выполняем запрос к базе данных
    gifts = await db.fetch(query, *params)

    # Преобразуем результаты
    result = []
    for gift in gifts:
        result.append(
            {
                "id": gift["id"],
                "event_time": (
                    gift["event_time"].isoformat() if gift["event_time"] else None
                ),
                "unique_id": gift["unique_id"],
                "gift_name": gift["gift_name"],
                "gift_count": gift["gift_count"],
                "diamond_count": gift["diamond_count"],
                "total_diamonds": gift["total_diamonds"],
            }
        )

    return {"donations": result}


@router.get("/api/profile/{streamer_id}/donators")
async def get_streamer_donators(
    streamer_id: int, period: str = Query("all", enum=["all", "month", "week", "day"])
):
    """API для получения донатеров стримера"""
    # Получаем информацию о стримере
    streamer = await db.fetchrow(
        "SELECT id, tik_tok_user_id FROM streamers WHERE id = $1", streamer_id
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    # Подготавливаем запрос на основе выбранного периода
    query = """
    SELECT g.unique_id, 
           COUNT(*) as donation_count,
           SUM(g.gift_count) as gift_count,
           SUM(g.diamond_count * g.gift_count) as diamond_count
    FROM gifts g
    WHERE g.streamer_id = $1
    """

    params = [streamer_id]

    if period == "month":
        # За текущий месяц
        query += (
            " AND DATE_TRUNC('month', g.event_time) = DATE_TRUNC('month', CURRENT_DATE)"
        )
    elif period == "week":
        # За текущую неделю
        query += (
            " AND DATE_TRUNC('week', g.event_time) = DATE_TRUNC('week', CURRENT_DATE)"
        )
    elif period == "day":
        # За сегодня
        query += " AND DATE_TRUNC('day', g.event_time) = CURRENT_DATE"

    query += " GROUP BY g.unique_id ORDER BY diamond_count DESC LIMIT 100"

    # Выполняем запрос к базе данных
    donators = await db.fetch(query, *params)

    # Преобразуем результаты
    result = []
    for donator in donators:
        result.append(
            {
                "unique_id": donator["unique_id"],
                "donation_count": donator["donation_count"],
                "gift_count": donator["gift_count"],
                "diamond_count": donator["diamond_count"],
            }
        )

    return {"donators": result}


@router.get("/api/profile/{streamer_id}/streams")
async def get_streamer_streams(streamer_id: int):
    """API для получения истории стримов"""
    # Получаем информацию о стримере
    streamer = await db.fetchrow(
        "SELECT id, tik_tok_user_id FROM streamers WHERE id = $1", streamer_id
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    # Выполняем запрос к базе данных
    streams = await db.fetch(
        """
        SELECT s.id, s.start_time, s.end_time, s.max_viewers, 
               s.total_diamonds, s.total_gifts
        FROM streams s
        WHERE s.streamer_id = $1
        ORDER BY s.start_time DESC
        LIMIT 100
        """,
        streamer_id,
    )

    # Преобразуем результаты
    result = []
    for stream in streams:
        result.append(
            {
                "id": stream["id"],
                "start_time": (
                    stream["start_time"].isoformat() if stream["start_time"] else None
                ),
                "end_time": (
                    stream["end_time"].isoformat() if stream["end_time"] else None
                ),
                "max_viewers": stream["max_viewers"],
                "total_diamonds": stream["total_diamonds"],
                "total_gifts": stream["total_gifts"],
            }
        )

    return {"streams": result}


# Для routes/streamers.py


@router.get("/api/profile/{streamer_id}/stats")
async def get_streamer_stats(streamer_id: int):
    """API для получения статистики стримера"""
    # Получаем информацию о стримере
    streamer = await db.fetchrow(
        "SELECT id, tik_tok_user_id FROM streamers WHERE id = $1", streamer_id
    )

    if not streamer:
        raise HTTPException(status_code=404, detail="Стример не найден")

    # Статистика за все время
    all_time_stats = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as donation_count,
            SUM(gift_count) as total_gifts,
            SUM(diamond_count * gift_count) as total_diamonds,
            SUM(diamond_count * gift_count / 200.0) as total_dollars
        FROM gifts
        WHERE streamer_id = $1
        """,
        streamer_id,
    )

    # Статистика за текущий месяц
    month_stats = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as donation_count,
            SUM(gift_count) as total_gifts,
            SUM(diamond_count * gift_count) as total_diamonds,
            SUM(diamond_count * gift_count / 200.0) as total_dollars
        FROM gifts
        WHERE 
            streamer_id = $1 AND
            DATE_TRUNC('month', event_time) = DATE_TRUNC('month', CURRENT_DATE)
        """,
        streamer_id,
    )

    # Статистика за текущую неделю
    week_stats = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as donation_count,
            SUM(gift_count) as total_gifts,
            SUM(diamond_count * gift_count) as total_diamonds,
            SUM(diamond_count * gift_count / 200.0) as total_dollars
        FROM gifts
        WHERE 
            streamer_id = $1 AND
            DATE_TRUNC('week', event_time) = DATE_TRUNC('week', CURRENT_DATE)
        """,
        streamer_id,
    )

    # Статистика за сегодня
    today_stats = await db.fetchrow(
        """
        SELECT 
            COUNT(*) as donation_count,
            SUM(gift_count) as total_gifts,
            SUM(diamond_count * gift_count) as total_diamonds,
            SUM(diamond_count * gift_count / 200.0) as total_dollars
        FROM gifts
        WHERE 
            streamer_id = $1 AND
            DATE_TRUNC('day', event_time) = CURRENT_DATE
        """,
        streamer_id,
    )

    # Статистика по дням
    daily_stats = await db.fetch(
        """
        SELECT 
            DATE_TRUNC('day', event_time)::date as day,
            COUNT(*) as donation_count,
            SUM(gift_count) as total_gifts,
            SUM(diamond_count * gift_count) as total_diamonds,
            SUM(diamond_count * gift_count / 200.0) as total_dollars
        FROM gifts
        WHERE 
            streamer_id = $1 AND
            event_time >= CURRENT_DATE - INTERVAL '30 day'
        GROUP BY DATE_TRUNC('day', event_time)::date
        ORDER BY day DESC
        """,
        streamer_id,
    )

    # Преобразуем результаты в словари для удобства и обработки null значений
    daily_stats_list = []
    for stat in daily_stats:
        daily_stats_list.append(
            {
                "day": stat["day"].isoformat() if stat["day"] else None,
                "donation_count": stat["donation_count"] or 0,
                "total_gifts": stat["total_gifts"] or 0,
                "total_diamonds": stat["total_diamonds"] or 0,
                "total_dollars": float(stat["total_dollars"] or 0),
            }
        )

    return {
        "all_time": {
            "donation_count": all_time_stats["donation_count"] or 0,
            "total_gifts": all_time_stats["total_gifts"] or 0,
            "total_diamonds": all_time_stats["total_diamonds"] or 0,
            "total_dollars": float(all_time_stats["total_dollars"] or 0),
        },
        "month": {
            "donation_count": month_stats["donation_count"] or 0,
            "total_gifts": month_stats["total_gifts"] or 0,
            "total_diamonds": month_stats["total_diamonds"] or 0,
            "total_dollars": float(month_stats["total_dollars"] or 0),
        },
        "week": {
            "donation_count": week_stats["donation_count"] or 0,
            "total_gifts": week_stats["total_gifts"] or 0,
            "total_diamonds": week_stats["total_diamonds"] or 0,
            "total_dollars": float(week_stats["total_dollars"] or 0),
        },
        "today": {
            "donation_count": today_stats["donation_count"] or 0,
            "total_gifts": today_stats["total_gifts"] or 0,
            "total_diamonds": today_stats["total_diamonds"] or 0,
            "total_dollars": float(today_stats["total_dollars"] or 0),
        },
        "daily_stats": daily_stats_list,
    }
