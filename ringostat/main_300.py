import asyncio
import aiohttp
import json
import logging
import signal
from tqdm import tqdm

API_URL = "https://185.233.116.213:5000/contact"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def generate_client_data(client_id):
    """Генерирует данные клиента на основе идентификатора."""
    return {
        "contactId": None,
        "mode": "new",
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
                "email": f"contact{client_id}@example.com",
            }
        ],
        "messengersData": [{"messenger": "Telegram", "link": f"t.me/user{client_id}"}],
        "paymentDetails": [
            {
                "IBAN": f"IBAN{client_id:010d}",
                "bankName": "Bank yo",
                "SWIFT": f"SWIFT{client_id:04d}",
                "accountType": "Two",
                "currency": "USD",
            }
        ],
    }


async def create_client(session, client_data, semaphore, progress, max_retries=3):
    """Создает клиента с обработкой повторных попыток и ошибок."""
    async with semaphore:
        retries = 0
        while retries < max_retries:
            try:
                headers = {"Content-Type": "application/json"}
                async with session.post(
                    API_URL, headers=headers, json=client_data, ssl=False
                ) as response:
                    if response.status in (200, 201):
                        # Успешно создано
                        await response.text()
                        break  # Выход из цикла повторов
                    elif response.status == 429:
                        # Превышен лимит запросов
                        # logging.warning(
                        #     "Получен код 429: слишком много запросов. Повтор через некоторое время..."
                        # )
                        await asyncio.sleep(2**retries)  # Экспоненциальная задержка
                    else:
                        # Обработка других ошибок
                        text = await response.text()
                        # logging.error(f"Ошибка {response.status}: {text}")
                        break
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # logging.error(f"Сетевая ошибка: {e}. Повтор попытки...")
                await asyncio.sleep(2**retries)
            except Exception as e:
                # logging.exception(f"Неизвестная ошибка: {e}")
                break
            finally:
                if retries == max_retries - 1:
                    logging.error(
                        f"Не удалось создать клиента после {max_retries} попыток."
                    )
                retries += 1
                progress.update(1)


async def main(total_clients):
    """Основная функция для запуска создания клиентов."""
    concurrency = 100  # Количество одновременных запросов
    semaphore = asyncio.Semaphore(concurrency)
    timeout = aiohttp.ClientTimeout(
        total=None, connect=10, sock_read=30
    )  # Настройка таймаутов

    # Создание соединения с отключенной проверкой SSL (требуется осторожность)
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        progress = tqdm(total=total_clients, desc="Создание клиентов", unit="клиентов")
        batch_size = concurrency * 10  # Размер пакета для обработки

        # Обработка сигналов для корректного завершения
        stop_event = asyncio.Event()

        def signal_handler():
            # logging.info("Получен сигнал остановки. Завершение работы...")
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_event_loop().add_signal_handler(sig, signal_handler)

        try:
            for batch_start in range(1, total_clients + 1, batch_size):
                tasks = []
                for client_id in range(
                    batch_start, min(batch_start + batch_size, total_clients + 1)
                ):
                    client_data = generate_client_data(client_id)
                    task = asyncio.create_task(
                        create_client(session, client_data, semaphore, progress)
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks)

                if stop_event.is_set():
                    # logging.info("Остановка по запросу пользователя.")
                    break

        finally:
            progress.close()


if __name__ == "__main__":
    TOTAL_CLIENTS = 290000  # Общее количество клиентов
    asyncio.run(main(TOTAL_CLIENTS))
