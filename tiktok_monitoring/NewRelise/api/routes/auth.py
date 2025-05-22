from datetime import timedelta
from typing import Optional

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_user_from_cookie,
    get_password_hash,
    get_user_by_username,
)
from database import db
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Страница входа
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Обработка входа
@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    user = await authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверное имя пользователя или пароль"},
        )

    # Проверка статуса одобрения (если используется)
    if hasattr(user, "approval_status") and user["approval_status"] == "pending":
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Ваша учетная запись ожидает одобрения администратором.",
            },
        )

    # Обновляем время последнего входа
    await db.execute("UPDATE users SET last_login = NOW() WHERE id = $1", user["id"])

    # Создаем JWT токен с четким назначением
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "type": "access"},
        expires_delta=access_token_expires,
    )

    # Устанавливаем токен в cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )

    return response


# ВАЖНО: Исправляем маршрут logout
@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response


# Регистрация (страница)
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# Регистрация (обработка)
@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: Optional[str] = Form(None),
):
    # Проверяем, существует ли пользователь
    existing_user = await get_user_by_username(username)
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пользователь с таким именем уже существует"},
        )

    # Хешируем пароль и создаем пользователя
    hashed_password = get_password_hash(password)

    # Создаем пользователя в БД
    try:
        await db.execute(
            """
            INSERT INTO users (username, password_hash, email, role, is_active)
            VALUES ($1, $2, $3, $4, $5)
            """,
            username,
            hashed_password,
            email,
            "user",
            True,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Ошибка при регистрации: {str(e)}"},
        )

    # Перенаправляем на страницу входа
    return RedirectResponse(url="/login?registered=1", status_code=303)


# Защищенный маршрут для проверки авторизации
@router.get("/protected")
async def protected(user=Depends(get_current_active_user)):
    return {"username": user["username"], "role": user["role"]}


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, current_user=Depends(get_current_active_user)):
    # Проверяем, что пользователь - администратор
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Получаем всех пользователей
    users = await db.fetch(
        """
        SELECT id, username, email, role, is_active, approval_status, created_at, last_login
        FROM users
        ORDER BY 
            CASE approval_status 
                WHEN 'pending' THEN 1 
                WHEN 'approved' THEN 2 
                WHEN 'rejected' THEN 3 
            END,
            created_at DESC
        """
    )

    return templates.TemplateResponse(
        "admin_users.html", {"request": request, "users": users}
    )


@router.post("/admin/users/{user_id}/approve")
async def approve_user(user_id: int, current_user=Depends(get_current_active_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    await db.execute(
        """
        UPDATE users 
        SET approval_status = 'approved', is_active = TRUE 
        WHERE id = $1
        """,
        user_id,
    )

    return RedirectResponse("/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/reject")
async def reject_user(user_id: int, current_user=Depends(get_current_active_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    await db.execute(
        """
        UPDATE users 
        SET approval_status = 'rejected', is_active = FALSE 
        WHERE id = $1
        """,
        user_id,
    )

    return RedirectResponse("/admin/users", status_code=303)
