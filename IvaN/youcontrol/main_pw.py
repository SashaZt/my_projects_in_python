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
html_directory = current_directory / "html"
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

input_csv_file = current_directory / "matched_urls.csv"
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
# Количество браузеров/потоков (теперь настраиваемо)
BROWSER_THREADS = 2  # Можно изменить на нужное количество


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


async def process_company(browser, edrpo, thread_id):
    """Обработка одной компании в существующем браузере."""
    try:
        # Проверяем, существует ли уже файл HTML для этой компании
        file_name = f"{edrpo}.html"
        file_path = html_directory / file_name
        if file_path.exists():
            logger.info(f"Файл {file_name} уже существует, пропускаем")
            return True  # Возвращаем True, чтобы компанию считали обработанной

        url = f"https://youcontrol.com.ua/catalog/company_details/{edrpo}/"

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

        try:
            # Используем domcontentloaded вместо networkidle - это работает быстрее
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Ждем элемент с таймаутом 5 секунд
            try:
                await page.wait_for_selector('//body[@class="seo-menu"]', timeout=5000)
            except Exception:
                logger.info(
                    f"Поток {thread_id}: элемент seo-menu не найден для {edrpo}, завершаем"
                )
                await context.close()
                return (
                    True  # Считаем компанию обработанной, чтобы не возвращать в очередь
                )

            content = await page.content()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Поток {thread_id}: страница {edrpo} загружена")

        except Exception as e:
            logger.warning(
                f"Поток {thread_id}: ошибка при загрузке страницы {edrpo}, но продолжаем: {e}"
            )
            await asyncio.sleep(3)
            await context.close()
            return False  # Вернем в очередь для повторной попытки

        # Закрываем только контекст, сохраняя браузер
        await context.close()
        return True

    except Exception as e:
        logger.error(
            f"Общая ошибка при обработке компании {edrpo} в потоке {thread_id}: {e}"
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
        return df["url"].tolist()
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
    for i in range(BROWSER_THREADS):  # Используем настраиваемое количество потоков
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


if __name__ == "__main__":
    # Сбор данных с сайта
    main()
