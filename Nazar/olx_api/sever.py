from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
from fastapi.middleware.cors import CORSMiddleware
from configuration.logger_setup import logger
import uuid

app = FastAPI()

# Хранилище для state (можно заменить на Redis или базу данных)
STATE_STORAGE = {}

CLIENT_ID = "202045"
CLIENT_SECRET = "QTrv3f3H2FIz06ADCOYXNulHV6gFRCp3031FRWJBny900Ffj"
REDIRECT_URI = "https://185.233.116.213:5000/auth/connect"
TOKEN_URL = "https://www.olx.ua/api/open/oauth/token"

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых источников
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],  # Явно указать методы
    allow_headers=["Authorization", "Content-Type"],  # Явно указать заголовки
)


@app.get("/start_auth")
async def start_auth():
    state = str(uuid.uuid4())
    logger.info(f"Generated state: {state}")
    STATE_STORAGE[state] = True  # Сохраняем state
    auth_url = (
        f"https://www.olx.ua/oauth/authorize/?"
        f"client_id={CLIENT_ID}&response_type=code&state={state}&scope=read+write+v2&redirect_uri={REDIRECT_URI}"
    )
    logger.info(f"Authorization URL: {auth_url}")
    return {"auth_url": auth_url, "state": state}


@app.get("/auth/connect")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    if not state or state not in STATE_STORAGE:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    del STATE_STORAGE[state]

    # Логируем полученные значения
    logger.info(f"Received code: {code}, state: {state}")

    # Выполняем обмен `code` на `access_token`
    token_data = await exchange_code_for_token(code)
    return JSONResponse(content={"access_token": token_data})


async def exchange_code_for_token(code: str):
    """
    Обменивает authorization code на access token.
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "read write v2",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Token request failed: {e.response.status_code}, {e.response.text}"
            )
            raise HTTPException(
                status_code=e.response.status_code, detail=e.response.text
            )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        ssl_keyfile="server.key",  # Укажите пути к вашим SSL-файлам
        ssl_certfile="server.crt",
    )
