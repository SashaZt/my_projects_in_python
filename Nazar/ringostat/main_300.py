import asyncio
import random
import string

import httpx
from tqdm import tqdm  # Для отображения прогресса

# Адрес сервера
BASE_URL = "https://185.233.116.213:5000/contact"


# Генерация случайных данных для записи
def generate_random_contact():
    return {
        "username": "".join(random.choices(string.ascii_letters, k=10)),
        "contact_type": random.choice(["Individual", "Company"]),
        "contact_status": random.choice(["New", "Updated"]),
        "manager": "".join(random.choices(string.ascii_letters, k=8)),
        "userphone": f"+{random.randint(100000000, 999999999)}",
        "useremail": f"{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com",
        "usersite": f"http://{''.join(random.choices(string.ascii_lowercase, k=5))}.com",
        "comment": "This is a test contact.",
    }


# Функция для отправки одного запроса
async def post_contact(client, contact_data):
    try:
        response = await client.post(BASE_URL, json=contact_data, timeout=10.0)
        if response.status_code != 200:
            print(f"Failed to post contact: {response.text}")
    except Exception as e:
        print(f"Exception during request: {e}")


# Функция для параллельной отправки запросов
async def post_contacts_concurrently(total_contacts, batch_size=100):
    async with httpx.AsyncClient(verify=False) as client:
        for _ in tqdm(range(0, total_contacts, batch_size), desc="Uploading contacts"):
            tasks = [
                post_contact(client, generate_random_contact())
                for _ in range(batch_size)
            ]
            await asyncio.gather(*tasks)


# Запуск записи 300 тысяч записей
if __name__ == "__main__":
    TOTAL_CONTACTS = 300_000
    asyncio.run(post_contacts_concurrently(TOTAL_CONTACTS, batch_size=500))
