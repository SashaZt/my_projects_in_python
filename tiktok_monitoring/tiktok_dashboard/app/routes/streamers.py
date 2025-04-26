# /app/routes/str
from typing import Optional

from database import db
from fastapi import APIRouter, Depends, Form, HTTPException, Request
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


@router.get("/", response_class=HTMLResponse)
async def list_streamers(request: Request):
    """Список стримеров"""
    streamers = await db.fetch(
        """
        SELECT s.id, ttu.name, s.room_id, c.name as cluster_name, 
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


@router.post("/add")
async def add_streamer(
    name: str = Form(...), cluster_id: int = Form(...), check_online: int = Form(30)
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
                user_id = existing_user["id"]
                # Проверяем, не привязан ли уже этот пользователь к стримеру
                existing_streamer = await conn.fetchval(
                    "SELECT id FROM streamers WHERE tik_tok_user_id = $1", user_id
                )
                if existing_streamer:
                    raise HTTPException(
                        status_code=400, detail="Стример с таким именем уже существует"
                    )
            else:
                # Создаем нового пользователя TikTok
                user_id = await conn.fetchval(
                    """
                    INSERT INTO tik_tok_users (name) 
                    VALUES ($1)
                    RETURNING id
                    """,
                    formatted_name,
                )

            # Создаем запись о стримере
            await conn.execute(
                """
                INSERT INTO streamers (tik_tok_user_id, cluster_id, status, check_online) 
                VALUES ($1, $2, $3, $4)
                """,
                user_id,
                cluster_id,
                "Запущен",
                check_online,
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
