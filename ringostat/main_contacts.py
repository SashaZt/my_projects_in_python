import asyncio
import aiohttp
import json
from tqdm import tqdm

API_URL = 'https://185.233.116.213:5000/contact'

def generate_client_data(client_id):
    return {
        "username": f"User{client_id}",
        "contactType": "Фіз.особа",
        "contactStatus": "Перший контакт",
        "manager": f"Менеджер {client_id}",
        "userphone": f"098{client_id:07d}",
        "useremail": f"user{client_id}@example.com",
        "usersite": f"https://site{client_id}.com",
        "comment": "Автоматическая запись",
        "additionalContacts": [
            {
                "name": f"Contact{client_id}",
                "position": "Manager",
                "phone": f"111-222-{client_id:04d}",
                "email": f"contact{client_id}@example.com"
            }
        ],
        "messengersData": [
            {
                "messenger": "Telegram",
                "link": f"t.me/user{client_id}"
            }
        ],
        "paymentDetails": [
            {
                "IBAN": f"IBAN{client_id:010d}",
                "bankName": "Bank yo",
                "SWIFT": f"SWIFT{client_id:04d}",
                "accountType": "Two",
                "currency": "USD"
            }
        ]
    }

async def create_client(session, client_data, semaphore, progress):
    async with semaphore:
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            async with session.post(API_URL, headers=headers, data=json.dumps(client_data), ssl=False) as response:
                if response.status == 201:
                    # Успешно создано
                    await response.text()
                else:
                    # Обработка ошибок
                    text = await response.text()
                    print(f"Ошибка {response.status}: {text}")
        except Exception as e:
            print(f"Исключение: {e}")
        finally:
            progress.update(1)

async def main(total_clients):
    concurrency = 10  # Количество одновременных запросов
    semaphore = asyncio.Semaphore(concurrency)
    timeout = aiohttp.ClientTimeout(total=60)  # Таймаут для запросов

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []
        progress = tqdm(total=total_clients, desc="Создание клиентов")

        for client_id in range(1, total_clients + 1):
            client_data = generate_client_data(client_id)
            task = asyncio.create_task(create_client(session, client_data, semaphore, progress))
            tasks.append(task)

        await asyncio.gather(*tasks)
        progress.close()

if __name__ == '__main__':
    TOTAL_CLIENTS = 1000  # Общее количество клиентов
    asyncio.run(main(TOTAL_CLIENTS))
