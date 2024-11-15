import base64
import os
from datetime import datetime

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from dependencies import get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

# Создание экземпляра маршрутизатора
router = APIRouter()

# Загрузка ключей из .env
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

SECRET_AES_KEY = os.getenv(
    "SECRET_AES_KEY"
).encode()  # Байтовый ключ для шифрования/расшифровки
ORIGINAL_ACCESS_KEY = os.getenv("ORIGINAL_ACCESS_KEY")  # Текстовый ключ для проверки


def decrypt_access_key(encrypted_key: str) -> str:
    encrypted_data = base64.b64decode(encrypted_key)
    iv = encrypted_data[:16]  # IV занимает первые 16 байтов
    ciphertext = encrypted_data[16:]

    cipher = Cipher(
        algorithms.AES(SECRET_AES_KEY), modes.CBC(iv), backend=default_backend()
    )
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # Убираем паддинг
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return (unpadder.update(padded_data) + unpadder.finalize()).decode()


@router.get("/get_all_data")
async def get_all_data(access_key: str = Query(...), db=Depends(get_db)):
    try:
        decrypted_key = decrypt_access_key(access_key)
        if decrypted_key != ORIGINAL_ACCESS_KEY:
            raise HTTPException(
                status_code=403, detail="Access denied: Invalid access key"
            )

        async with db.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM calls_zubr")
                records = await cursor.fetchall()

        for record in records:
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = value.strftime("%Y-%m-%d %H:%M:%S")

        return JSONResponse(
            status_code=200, content={"status": "success", "data": records}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "failure", "message": str(e)}
        )
