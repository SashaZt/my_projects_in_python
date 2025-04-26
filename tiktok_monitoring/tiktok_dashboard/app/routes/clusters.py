# app/routes/clusters.py
from database import db
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter()
templates = Jinja2Templates(directory="templates")


class ClusterCreate(BaseModel):
    name: str
    description: str = None


class ClusterUpdate(BaseModel):
    name: str
    description: str = None


@router.get("/", response_class=HTMLResponse)
async def list_clusters(request: Request):
    """Страница со списком кластеров"""
    # Получаем кластеры вместе с количеством стримеров в каждом
    clusters = await db.fetch(
        """
        SELECT c.id, c.name, c.description, COUNT(s.id) as streamer_count
        FROM clusters c
        LEFT JOIN streamers s ON c.id = s.cluster_id
        GROUP BY c.id, c.name, c.description
        ORDER BY c.name
        """
    )

    return templates.TemplateResponse(
        "clusters.html", {"request": request, "clusters": clusters}
    )


@router.get("/add", response_class=HTMLResponse)
async def add_cluster_form(request: Request):
    """Форма добавления кластера"""
    return templates.TemplateResponse("cluster_add.html", {"request": request})


@router.post("/add")
async def add_cluster(name: str = Form(...), description: str = Form("")):
    """Обработка формы добавления кластера"""
    # Проверяем, существует ли уже такой кластер
    existing = await db.fetchval("SELECT id FROM clusters WHERE name = $1", name)

    if existing:
        raise HTTPException(
            status_code=400, detail="Кластер с таким именем уже существует"
        )

    # Создаем новый кластер
    await db.execute(
        """
        INSERT INTO clusters (name, description) 
        VALUES ($1, $2)
        """,
        name,
        description,
    )

    return RedirectResponse(url="/clusters", status_code=303)


@router.get("/edit/{cluster_id}", response_class=HTMLResponse)
async def edit_cluster_form(request: Request, cluster_id: int):
    """Форма редактирования кластера"""
    cluster = await db.fetchrow(
        "SELECT id, name, description FROM clusters WHERE id = $1", cluster_id
    )

    if not cluster:
        raise HTTPException(status_code=404, detail="Кластер не найден")

    return templates.TemplateResponse(
        "cluster_edit.html", {"request": request, "cluster": cluster}
    )


@router.post("/edit/{cluster_id}")
async def edit_cluster(
    cluster_id: int, name: str = Form(...), description: str = Form("")
):
    """Обработка формы редактирования кластера"""
    # Проверяем, существует ли кластер
    cluster = await db.fetchrow("SELECT id FROM clusters WHERE id = $1", cluster_id)

    if not cluster:
        raise HTTPException(status_code=404, detail="Кластер не найден")

    # Проверяем, существует ли уже кластер с таким именем (кроме текущего)
    existing = await db.fetchval(
        "SELECT id FROM clusters WHERE name = $1 AND id != $2", name, cluster_id
    )

    if existing:
        raise HTTPException(
            status_code=400, detail="Кластер с таким именем уже существует"
        )

    # Обновляем кластер
    await db.execute(
        """
        UPDATE clusters 
        SET name = $1, description = $2
        WHERE id = $3
        """,
        name,
        description,
        cluster_id,
    )

    return RedirectResponse(url="/clusters", status_code=303)


@router.delete("/{cluster_id}")
async def delete_cluster(cluster_id: int):
    """Удаление кластера"""
    # Проверяем, существует ли кластер
    cluster = await db.fetchrow("SELECT id FROM clusters WHERE id = $1", cluster_id)

    if not cluster:
        raise HTTPException(status_code=404, detail="Кластер не найден")

    # Проверяем, есть ли стримеры в этом кластере
    streamers_count = await db.fetchval(
        "SELECT COUNT(*) FROM streamers WHERE cluster_id = $1", cluster_id
    )

    if streamers_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Невозможно удалить кластер. В нем есть {streamers_count} стримеров.",
        )

    # Удаляем кластер
    await db.execute("DELETE FROM clusters WHERE id = $1", cluster_id)

    return {"status": "success"}
