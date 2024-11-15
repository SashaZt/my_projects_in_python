# client_get_data.py
import base64
import os

import requests
import urllib3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from dotenv import load_dotenv

# Укажите точный путь к .env файлу, если он не загружается автоматически
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
# Попробуйте получить ключи с проверкой на None
SECRET_AES_KEY = os.getenv("SECRET_AES_KEY")
ORIGINAL_ACCESS_KEY = os.getenv("ORIGINAL_ACCESS_KEY")

if SECRET_AES_KEY is None or ORIGINAL_ACCESS_KEY is None:
    raise ValueError("SECRET_AES_KEY или ORIGINAL_ACCESS_KEY не найдены в .env файле")

# Преобразуем SECRET_AES_KEY в байты
SECRET_AES_KEY = SECRET_AES_KEY.encode()  # Ключ для шифрования (32 байта)


def encrypt_access_key(access_key: str) -> str:
    # Генерация случайного 16-байтового IV
    iv = os.urandom(16)

    # Паддинг для обеспечения кратности 16 байтам
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(access_key.encode()) + padder.finalize()

    # Шифрование с использованием SECRET_AES_KEY и сгенерированного iv
    cipher = Cipher(
        algorithms.AES(SECRET_AES_KEY),
        modes.CBC(iv),
        backend=default_backend(),
    )
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Кодируем IV и зашифрованные данные в base64 для передачи
    return base64.b64encode(iv + encrypted_data).decode()


def fetch_all_data():
    url = "https://185.233.116.213:5000/get_all_data"
    encrypted_key = encrypt_access_key(
        ORIGINAL_ACCESS_KEY
    )  # Шифруем исходный access_key

    params = {"access_key": encrypted_key}
    try:
        response = requests.get(url, params=params, verify=False)
        if response.status_code == 200:
            print("Data fetched successfully:")
            print(response.json())
        else:
            print(f"Failed to fetch data, status code: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    fetch_all_data()
