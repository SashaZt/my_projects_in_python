import asyncio
import json
import queue
import random
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

import aiofiles
import pandas as pd
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Response, async_playwright

# Настройка директорий
current_directory = Path.cwd()
data_directory = current_directory / "data"
log_directory = current_directory / "log"
json_directory = current_directory / "json"
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

input_csv_file = data_directory / "output.csv"
log_file_path = log_directory / "log_message.log"
proxy_file = config_directory / "roman.txt"

# Настройка логирования
logger.remove()
# Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

# Очередь для компаний
company_queue = queue.Queue()
# Флаг для остановки потоков
stop_threads = False
# Блокировка для доступа к общим ресурсам
lock = threading.Lock()
# Словарь для хранения информации о браузерах
browser_pool = {}
# Максимальное количество браузеров
MAX_BROWSERS = 10


async def load_proxies() -> list:
    """Загрузка прокси из файла."""
    if not proxy_file.exists():
        logger.info(f"Файл прокси {proxy_file} не найден. Запускаем без прокси.")
        return []

    try:
        async with aiofiles.open(proxy_file, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in await file.readlines() if line.strip()]
        logger.info(f"Загружено {len(proxies)} прокси")
        return proxies
    except Exception as e:
        logger.error(f"Ошибка загрузки прокси: {e}")
        return []


def parse_proxy(proxy: str) -> Dict:
    """Парсинг строки прокси в конфигурацию."""
    try:
        if "@" in proxy:
            protocol, rest = proxy.split("://", 1)
            credentials, server = rest.split("@", 1)
            username, password = credentials.split(":", 1)
            return {
                "server": f"{protocol}://{server}",
                "username": username,
                "password": password,
            }
        return {"server": f"http://{proxy}"}
    except Exception as e:
        logger.error(f"Ошибка парсинга прокси {proxy}: {e}")
        return None


async def save_json_response(data: dict, json_file):
    """Сохранение JSON ответа в файл."""
    try:
        async with aiofiles.open(json_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        logger.info(f"JSON ответ сохранен в {json_file}")
    except Exception as e:
        logger.error(f"Ошибка сохранения JSON ответа: {e}")


async def handle_response(response: Response, json_file):
    """Обработка ответов от сервера."""
    try:
        if "https://pk-api.adata.kz/api/v1/data/company/tax/graph/bar" in response.url:
            headers = await response.all_headers()
            if "application/json" in headers.get("content-type", ""):
                logger.info(f"Перехвачен JSON ответ от {response.url}")
                json_data = await response.json()
                await save_json_response(json_data, json_file)
                logger.info("JSON ответ перехвачен и сохранен")
    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}")


async def init_browser(playwright, thread_id):
    """Инициализация браузера для потока."""
    try:
        # Загружаем прокси
        proxies = await load_proxies()
        proxy_config = None

        if proxies:
            proxy = random.choice(proxies)
            proxy_config = parse_proxy(proxy)
            logger.info(f"Поток {thread_id} использует прокси: {proxy}")
        else:
            logger.info(f"Поток {thread_id} запущен без прокси")

        browser_args = {
            "headless": False,  # Показывать браузер
        }

        if proxy_config:
            browser_args["proxy"] = proxy_config

        browser = await playwright.chromium.launch(**browser_args)

        logger.info(f"Поток {thread_id} успешно инициализировал новый браузер")
        return browser

    except Exception as e:
        logger.error(f"Ошибка при инициализации браузера в потоке {thread_id}: {e}")
        return None


async def process_company(browser, company, thread_id):
    """Обработка одной компании в существующем браузере."""
    try:
        # Проверяем, существует ли уже файл JSON для этой компании
        json_file = json_directory / f"{company}.json"
        if json_file.exists():
            logger.info(f"Файл {json_file} уже существует, пропускаем")
            return True

        url = f"https://pk.adata.kz/company/{company}"

        # Создаем новый контекст для вкладки с отключенными изображениями и другими оптимизациями
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        # Отключаем загрузку изображений, шрифтов и других медиафайлов
        await context.route(
            "**/*",
            lambda route, request: (
                route.abort()
                if request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            ),
        )
        page = await context.new_page()

        # Подписываемся на события ответа
        page.on(
            "response",
            lambda response: asyncio.ensure_future(
                handle_response(response, json_file)
            ),
        )

        try:
            logger.info(f"Поток {thread_id}: переход по URL: {url}")

            # Устанавливаем флаг для отслеживания успешной загрузки JSON
            json_loaded = False

            # Устанавливаем обработчик для отслеживания нужного ответа API
            async def check_response(response):
                nonlocal json_loaded
                try:
                    if (
                        "https://pk-api.adata.kz/api/v1/data/company/tax/graph/bar"
                        in response.url
                    ):
                        headers = await response.all_headers()
                        if "application/json" in headers.get("content-type", ""):
                            json_loaded = True
                            logger.info(
                                f"Поток {thread_id}: обнаружен нужный JSON для {company}"
                            )
                except Exception as e:
                    logger.error(f"Ошибка при проверке ответа: {e}")

            # Временно добавляем обработчик для отслеживания загрузки JSON
            page.on("response", check_response)

            try:
                # Используем domcontentloaded вместо networkidle - это работает быстрее
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
                logger.info(f"Поток {thread_id}: страница {company} загружена")

                # Ждем некоторое время для загрузки API
                for _ in range(10):  # Максимум 10 секунд ожидания
                    if json_loaded:
                        break
                    await asyncio.sleep(1)

                # Если JSON не загрузился, но страница открылась - это всё равно успех
                if not json_loaded:
                    logger.warning(
                        f"Поток {thread_id}: JSON для {company} не был загружен, но продолжаем"
                    )

            except Exception as e:
                logger.warning(
                    f"Поток {thread_id}: ошибка при загрузке страницы {company}, но продолжаем: {e}"
                )
                # Проверим, был ли загружен JSON несмотря на ошибку
                if json_loaded:
                    logger.info(
                        f"Поток {thread_id}: JSON для {company} был успешно загружен несмотря на ошибку"
                    )
                    # Возвращаем True, так как основная цель достигнута
                    return True
                await asyncio.sleep(3)

            # Закрываем только контекст, сохраняя браузер
            await context.close()

            return True

        except Exception as e:
            logger.error(
                f"Ошибка при обработке компании {company} в потоке {thread_id}: {e}"
            )
            # Закрываем контекст при ошибке
            await context.close()
            return False

    except Exception as e:
        logger.error(
            f"Общая ошибка при обработке компании {company} в потоке {thread_id}: {e}"
        )
        return False


async def worker_task(thread_id):
    """Асинхронная задача для работы с браузером."""
    logger.info(f"Запущен поток {thread_id}")

    try:
        async with async_playwright() as playwright:
            # Инициализируем браузер для этого потока
            browser = await init_browser(playwright, thread_id)

            if not browser:
                logger.error(
                    f"Не удалось создать браузер в потоке {thread_id}. Завершаем поток."
                )
                return

            with lock:
                browser_pool[thread_id] = {
                    "browser": browser,
                    "active": True,
                    "last_activity": time.time(),
                }

            logger.info(f"Браузер для потока {thread_id} успешно добавлен в пул")

            while not stop_threads:
                try:
                    # Получаем компанию из очереди
                    try:
                        company = company_queue.get(timeout=5)
                    except queue.Empty:
                        if stop_threads:
                            break
                        # Проверка жизни браузера и перезапуск при необходимости
                        try:
                            await browser.contexts()  # Проверяем, что браузер еще жив
                            await asyncio.sleep(1)
                            continue
                        except Exception:
                            logger.warning(
                                f"Браузер в потоке {thread_id} не отвечает, перезапускаем"
                            )
                            try:
                                await browser.close()
                            except:
                                pass
                            browser = await init_browser(playwright, thread_id)
                            if not browser:
                                logger.error(
                                    f"Не удалось перезапустить браузер в потоке {thread_id}. Завершаем поток."
                                )
                                return
                            continue

                    logger.info(f"Поток {thread_id} обрабатывает компанию {company}")

                    # Обновляем время последней активности
                    with lock:
                        if thread_id in browser_pool:
                            browser_pool[thread_id]["last_activity"] = time.time()

                    # Обрабатываем компанию
                    success = await process_company(browser, company, thread_id)

                    if success:
                        logger.info(
                            f"Успешно обработана компания {company} в потоке {thread_id}"
                        )
                        company_queue.task_done()
                    else:
                        logger.error(
                            f"Не удалось обработать компанию {company} в потоке {thread_id}, возвращаем в очередь"
                        )
                        company_queue.put(company)
                        # Небольшая задержка перед повторной попыткой
                        await asyncio.sleep(5)
                        company_queue.task_done()

                except Exception as e:
                    logger.error(f"Ошибка в потоке {thread_id}: {e}")
                    # Перезапускаем браузер при критической ошибке
                    try:
                        await browser.close()
                    except:
                        pass

                    browser = await init_browser(playwright, thread_id)
                    if not browser:
                        logger.error(
                            f"Не удалось перезапустить браузер в потоке {thread_id} после ошибки. Завершаем поток."
                        )
                        return

                    # Небольшая пауза между попытками
                    await asyncio.sleep(2)

            # Закрываем браузер при выходе из цикла
            try:
                await browser.close()
                logger.info(f"Браузер в потоке {thread_id} закрыт")
            except:
                pass

            with lock:
                if thread_id in browser_pool:
                    browser_pool[thread_id]["active"] = False

    except Exception as e:
        logger.error(f"Критическая ошибка в потоке {thread_id}: {e}")

    finally:
        logger.info(f"Поток {thread_id} завершен")


def thread_runner(thread_id):
    """Функция-обертка для запуска асинхронной задачи в потоке."""
    asyncio.run(worker_task(thread_id))


# Функция для чтения ID компаний из CSV файла
def read_companies_from_csv(input_csv_file):
    try:
        df = pd.read_csv(input_csv_file)
        return df["bin"].tolist()
    except Exception as e:
        logger.error(f"Ошибка при чтении CSV файла: {e}")
        return []


def main():
    global stop_threads

    # Получаем список ID компаний
    company_ids = read_companies_from_csv(input_csv_file)
    if not company_ids:
        logger.error("Не удалось получить список компаний из CSV файла")
        return

    logger.info(f"Загружено {len(company_ids)} компаний из CSV файла")

    # Загружаем компании в очередь
    for company_id in company_ids:
        company_queue.put(company_id)

    # Создаем и запускаем потоки
    threads = []
    for i in range(MAX_BROWSERS):
        thread = threading.Thread(target=thread_runner, args=(i,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        logger.info(f"Запущен поток {i}")
        # Небольшая пауза между запуском браузеров, чтобы не перегружать систему
        time.sleep(1)

    try:
        # Ждем завершения всех задач в очереди
        company_queue.join()
        logger.info("Все компании обработаны успешно")
    except KeyboardInterrupt:
        logger.info("Получен сигнал на остановку, завершаем работу...")
        stop_threads = True

    # Сигнализируем потокам о необходимости завершения
    stop_threads = True

    # Ждем завершения всех потоков
    for thread in threads:
        thread.join(timeout=30)

    logger.info("Скрипт завершил работу")


# def write_csv(data, output_file="company_data.csv"):
#     # Создаем DataFrame
#     df = pd.DataFrame(data)
#     # Сохраняем в CSV
#     df.to_csv(output_file, index=False, encoding="utf-8")
#     logger.info(f"Данные успешно записаны в {output_file}")


# def scrap_json():
#     all_data = []
#     for json_file in json_directory.glob("*.json"):
#         with open(json_file, "r", encoding="utf-8") as file:
#             data = json.load(file)

#         company_bin = json_file.stem

#         json_result_data = data.get("data", [])
#         if json_result_data:
#             json_result = data["data"]["result"]
#             json_meta = data["data"]["meta"]
#             relevance = json_meta["relevance"]


#             for data_year in json_result[-5:]:
#                 result = {
#                     "company_bin": company_bin,
#                     "Год": data_year["year"],
#                     "Сумма отчислений, ₸": data_year["amount"],
#                     "Сумма отчислений, %": data_year["percentage"],
#                     "Обязательные платежи с ФОТ, ₸": data_year["amount_fot"],
#                     "Обязательные платежи с ФОТ, %": data_year["percentage_fot"],
#                     "Налоги, ₸": data_year["amount_other"],
#                     "Налоги, %": data_year["percentage_other"],
#                     "relevance": relevance,
#                 }
#                 all_data.append(result)
#     logger.info(all_data)
#     return all_data
def write_csv(data, output_file="company_data_pivot.csv"):
    # Создаем DataFrame из всех данных
    df = pd.DataFrame(data)

    # Создаем сводную таблицу
    pivot_df = pd.pivot_table(
        df,
        index=["company_bin", "relevance"],  # Строки - компании и relevance
        columns="Год",  # Колонки - годы
        values=[
            "Сумма отчислений, ₸",
            "Сумма отчислений, %",
            "Обязательные платежи с ФОТ, ₸",
            "Обязательные платежи с ФОТ, %",
            "Налоги, ₸",
            "Налоги, %",
        ],
        fill_value=0,  # Заполняем пропуски нулями
    )

    # Преобразуем многоуровневые заголовки в плоские
    pivot_df.columns = [f"{year} {metric}" for metric, year in pivot_df.columns]

    # Сбрасываем индекс, чтобы company_bin и relevance стали колонками
    pivot_df = pivot_df.reset_index()

    # Сохраняем в CSV
    pivot_df.to_csv(output_file, index=False, encoding="utf-8")
    logger.info(f"Данные успешно записаны в {output_file}")


def scrap_json():
    all_data = []
    for json_file in json_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        company_bin = json_file.stem
        json_result_data = data.get("data", [])
        if json_result_data:
            json_result = data["data"]["result"]
            json_meta = data["data"]["meta"]
            relevance = json_meta["relevance"]

            for data_year in json_result[-5:]:
                result = {
                    "company_bin": company_bin,
                    "Год": data_year["year"],
                    "Сумма отчислений, ₸": data_year["amount"],
                    "Сумма отчислений, %": data_year["percentage"],
                    "Обязательные платежи с ФОТ, ₸": data_year["amount_fot"],
                    "Обязательные платежи с ФОТ, %": data_year["percentage_fot"],
                    "Налоги, ₸": data_year["amount_other"],
                    "Налоги, %": data_year["percentage_other"],
                    "relevance": relevance,
                }
                all_data.append(result)
    logger.info(all_data)
    return all_data


if __name__ == "__main__":
    # # Сбор данных с сайта
    # main()
    data = scrap_json()
    write_csv(data)
