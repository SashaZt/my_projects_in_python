from datetime import datetime, timedelta
from typing import Optional, Union

from database import db
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Настройки JWT - используем более простой подход
SECRET_KEY = "vQEf5xL3ZP#HWw^8s!q$rUg=6F4t@KdTm7*XJyC2a_N9pGn+Y-eR1bDzVMSi&h"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 день

# Настройка контекста хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


# Модель для токена
class Token(BaseModel):
    access_token: str
    token_type: str


# Модель для входа
class UserLogin(BaseModel):
    username: str
    password: str


# Проверка пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Хеширование пароля
def get_password_hash(password):
    return pwd_context.hash(password)


# Создание JWT токена
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Получение пользователя по имени
async def get_user_by_username(username: str):
    query = "SELECT * FROM users WHERE username = $1"
    user = await db.fetchrow(query, username)
    return user


# Аутентификация пользователя
async def authenticate_user(username: str, password: str):
    user = await get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user


# Получение текущего пользователя из токена
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недействительные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception

    return user


# Проверка активности пользователя
async def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")
    return current_user


# Извлечение токена из cookies
async def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    return token


# Получение текущего пользователя из cookies
async def get_current_user_from_cookie(token: str = Depends(get_token_from_cookie)):
    return await get_current_user(token)
