# client/main.py
import asyncio
import json
import httpx
import aiofiles
from pathlib import Path
from loguru import logger
import sys


current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)
# URL-шаблон запроса: {page} будет заменяться на номер страницы
URL_TEMPLATE = (
    "https://gettransfer.com/api/transfers?"
    "page={page}&role=carrier&filtering%5Bdate_since%5D=&filtering%5Bdate_till%5D="
    "&filtering%5Bsearch%5D=&filtering%5Boffers%5D=except_my&filtering%5Basap%5D=false"
    "&filtering%5Bhidden%5D=false&sorting%5Bfield%5D=created_at&sorting%5Border_by%5D=desc"
)

# Необходимые заголовки и cookies – заполните реальными значениями
HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8',
    'dnt': '1',
    'priority': 'u=1, i',
    'referer': 'https://gettransfer.com/ru/carrier/',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
}


COOKIES = {
    'locale': 'ru',
    'cookieAccepted': 'true',
    'rack.session': '7d455f84ae005c2474c86e22051d3bfaee8fe06ba0167f1a3ba33ef4f4dc4402',
    '__cf_bm': 'jyx.tGoMu4fO6NDWbSTTsfa5PM8uyCMa9GvmzupHqPI-1739713454-1.0.1.1-GJUt0POJLGaGCBVdDhvAAfd8yTNAjQNMwkDY.MpLWghXR3H6PT2oCHwiAPn3nBF3PxSfLhoAyOtkFpxasnqi_.TAB.AKSry9WAUYpyBhf2I',
    'cf_clearance': 'bKOUZ6Q2FdKfOHKIytTp2wRYbskB2o5DVAPOBIZU970-1739713455-1.2.1.1-QWOJOzj.IEdNpvJvKScPonAwX2MSTNBkf_GWa.L7VRNBfDZbsg2MuqgFSXE4Uf3FGgi13wyFx5hxS8QFR0TCB9ol8.9UF0B3LIqu9qzoGS5.3gxLn1qfd_h7Ds3DIv8SxSWQtsoOWffOVJrGMjA08rvqxyWRzplJDXd2Fjo8ULUyGpEhZIHoIqAtMNe4Rd4u4sXqvO4TKGJbcZ4fnRLth7TaFSVUn.xdjqx2aD5oSdripqIOYzJX8yYJtOqA2k0mvrE3Q1GrNAZFWx_gFV4lxtYwxSA4tHO8cZhJLJ99jUI',
    'io': 'GHrs8VqMH0t3Q7HNOsDm',
}

# API-эндпоинт вашего FastAPI, куда будут отправляться записи
API_ENDPOINT = "http://web:5000/transfer"


async def fetch_page(client: httpx.AsyncClient, page: int) -> dict:
    """Получить данные для конкретной страницы."""
    url = URL_TEMPLATE.format(page=page)
    try:
        logger.debug(f"Отправка GET-запроса на {url}")
        response = await client.get(url, headers=HEADERS, cookies=COOKIES)
        response.raise_for_status()
        logger.info(f"Данные для страницы {page} успешно получены")
        return response.json()
    except httpx.HTTPStatusError as http_err:
        logger.error(f"HTTP ошибка при получении страницы {page}: {http_err}")
    except httpx.RequestError as req_err:
        logger.error(f"Ошибка запроса при получении страницы {page}: {req_err}")
    except Exception as err:
        logger.error(f"Ошибка при получении страницы {page}: {err}")
    return {}


async def get_json() -> dict:
    """
    Асинхронно получить данные с внешнего сервиса.
    Если pages_count > 1 – выполнить дополнительные запросы для всех страниц,
    объединить данные и сохранить в файл output_json.json.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Получаем первую страницу
            first_page_data = await fetch_page(client, page=1)
            if not first_page_data:
                logger.error("Не удалось получить данные первой страницы")
                return {}

            # Если данные вложены в ключ "data", извлекаем его
            data_section = first_page_data.get("data", {})
            pages_count = data_section.get("pages_count", 1)
            logger.info(f"Обнаружено страниц: {pages_count}")

            # Извлекаем список трансферов
            all_data = data_section.get("transfers", [])

            # Если страниц больше 1 – делаем дополнительные запросы
            if pages_count > 1:
                tasks = [
                    fetch_page(client, page=page) for page in range(2, pages_count + 1)
                ]
                pages_results = await asyncio.gather(*tasks, return_exceptions=True)
                for idx, page_result in enumerate(pages_results, start=2):
                    if isinstance(page_result, dict) and page_result:
                        nested = page_result.get("data", {})
                        page_data = nested.get("transfers", [])
                        logger.debug(f"Страница {idx}: получено {len(page_data)} записей")
                        all_data.extend(page_data)
                    else:
                        logger.error(f"Ошибка при получении данных страницы {idx}")

            # Обновляем JSON: заменяем ключ "data" на объединённые данные
            first_page_data["data"] = {
                "transfers": all_data,
                "pages_count": pages_count
            }

            # Асинхронно сохраняем JSON в файл
            file_output = "output_json.json"
            async with aiofiles.open(file_output, "w", encoding="utf-8") as f:
                await f.write(json.dumps(first_page_data, ensure_ascii=False, indent=4))
            logger.info(f"JSON-файл успешно сохранен в {file_output}")
            return first_page_data
    except Exception as e:
        logger.error(f"Ошибка в get_json: {e}")
        return {}



async def scrap_json() -> list:
    """
    Асинхронно загрузить сохранённый JSON, обработать его и сформировать итоговый список записей.
    """
    try:
        async with aiofiles.open("output_json.json", "r", encoding="utf-8") as f:
            content = await f.read()
        data = json.loads(content)

        all_transfers = []  # Итоговый список для хранения обработанных записей
        # Извлекаем список трансферов из вложенного ключа "data"
        transfers = data.get("data", {}).get("transfers", [])

        for transfer in transfers:
            # Извлечение основных полей
            transfer_id = transfer.get("id")
            duration = transfer.get("duration")
            distance = transfer.get("distance")
            time_val = transfer.get("time")
            transfer_type = transfer.get("type")
            pax = transfer.get("pax")
            date_to_local = transfer.get("date_to_local")
            date_end_local = transfer.get("date_end_local")
            date_return_local = transfer.get("date_return_local")

            # Данные о месте отправления
            from_data = transfer.get("from", {}) or {}
            from_location = from_data.get("name")
            from_point = from_data.get("point")
            from_country = from_data.get("country")
            from_types = from_data.get("types")

            # Данные о месте назначения
            to_data = transfer.get("to", {}) or {}
            to_location = to_data.get("name")
            to_point = to_data.get("point")
            to_country = to_data.get("country")
            to_types = to_data.get("types")

            transport_type_ids = transfer.get("transport_type_ids", [])
            created_at = transfer.get("created_at")
            no_competitors = transfer.get("no_competitors")
            carrier_offer = transfer.get("carrier_offer")
            status = transfer.get("status")
            comment = transfer.get("comment", "")
            suggested_prices = transfer.get("suggested_prices", {})
            urgent = transfer.get("urgent")
            prices_output = [
                {"type": key.capitalize(), "amount": value.get("amount")}
                for key, value in suggested_prices.items()
            ]
            asap = transfer.get("asap", False)
            commission = transfer.get("commission", 0.0)
            uuid = transfer.get("uuid")
            offerable_for = transfer.get("offerable_for", 0)

            json_data = {
                "transfer_id": transfer_id,
                "duration": duration,
                "distance": distance,
                "time": time_val,
                "type": transfer_type,
                "transport_type_ids": transport_type_ids,
                "pax": pax,
                "date_to_local": date_to_local,
                "date_end_local": date_end_local,
                "date_return_local": date_return_local,
                "from_location": from_location,
                "from_point": from_point,
                "from_country": from_country,
                "from_types": from_types,
                "to_location": to_location,
                "to_point": to_point,
                "to_country": to_country,
                "to_types": to_types,
                "prices_output": prices_output,
                "status": status,
                "asap": asap,
                "commission": commission,
                "uuid": uuid,
                "comment": comment,
                "offerable_for": offerable_for,
                "created_at": created_at,
                "urgent": urgent,
                "no_competitors": no_competitors,
                "carrier_offer": carrier_offer,
            }
            all_transfers.append(json_data)

        # Сохраняем итоговые данные в файл output.json
        async with aiofiles.open("output.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(all_transfers, ensure_ascii=False, indent=4))
        logger.info("Данные успешно сохранены в output.json")
        return all_transfers
    except Exception as e:
        logger.error(f"Ошибка в scrap_json: {e}")
        return []


async def send_transfer(client: httpx.AsyncClient, transfer: dict):
    """
    Отправить запись трансфера на API вашего FastAPI для сохранения в БД.
    """
    try:
        logger.debug(f"Отправка POST-запроса на {API_ENDPOINT} с данными: {transfer}")
        response = await client.post(API_ENDPOINT, json=transfer)
        response.raise_for_status()
        logger.info(
            f"Запись трансфера с id={transfer.get('transfer_id')} успешно отправлена в API"
        )
    except httpx.HTTPStatusError as http_err:
        logger.error(
            f"HTTP ошибка при отправке трансфера с id={transfer.get('transfer_id')}: {http_err}"
        )
    except httpx.RequestError as req_err:
        logger.error(
            f"Ошибка запроса при отправке трансфера с id={transfer.get('transfer_id')}: {req_err}"
        )
    except Exception as err:
        logger.error(
            f"Ошибка при отправке трансфера с id={transfer.get('transfer_id')}: {err}"
        )


async def send_all_transfers(transfers: list):
    """
    Отправить все полученные трансферы на API.
    """
    async with httpx.AsyncClient() as client:
        tasks = [send_transfer(client, transfer) for transfer in transfers]
        await asyncio.gather(*tasks)


async def main():
    # Получаем JSON с внешнего сервиса и сохраняем его в output_json.json
    await get_json()
    # Обрабатываем сохранённый JSON и получаем список трансферов
    transfers = await scrap_json()
    if transfers:
        # Отправляем каждый трансфер на API для записи в БД
        await send_all_transfers(transfers)
    else:
        logger.error("Нет данных для отправки на API")


if __name__ == "__main__":

    async def run_with_pause():
        logger.info("Запуск скрипта")
        # await main()
        # Асинхронная пауза на 5 минут (300 секунд)
        await asyncio.sleep(300)

    asyncio.run(run_with_pause())
