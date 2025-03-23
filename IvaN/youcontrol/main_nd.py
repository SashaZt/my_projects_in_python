import asyncio
import datetime
import json
import os
import random
import sys
from pathlib import Path

import nodriver as uc
import numpy as np
import pandas as pd
from loguru import logger

# Количество потоков (задайте нужное количество)
NUM_THREADS = 5

# Список доступных прокси
PROXY_LIST = [
    "http://55304:1MxDHi0e@185.112.14.143:2831",
    "http://55304:1MxDHi0e@195.123.179.239:2831",
    "http://55304:1MxDHi0e@195.123.179.12:2831",
    "http://55304:1MxDHi0e@185.112.12.197:2831",
    "http://55304:1MxDHi0e@212.86.111.97:2831",
    "http://55304:1MxDHi0e@195.123.178.109:2831",
    "http://55304:1MxDHi0e@185.112.15.224:2831",
    "http://55304:1MxDHi0e@195.123.193.57:2831",
    "http://55304:1MxDHi0e@195.123.193.8:2831",
    "http://55304:1MxDHi0e@195.123.179.65:2831",
]

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


async def process_country(browser, edrpo):
    try:
        url = f"https://youcontrol.com.ua/catalog/company_details/{edrpo}/"
        # Сохраняем страницу
        file_path = html_directory / f"{edrpo}.html"
        if file_path.exists():
            logger.warning(f"Страница уже существует: {file_path}")
            return True
        # Переходим на страницу страны
        tab = await browser.get(url)
        await asyncio.sleep(1)
        await tab  # Обновляем страницу

        # Проверка на 404
        page_404 = await tab.select("#wrapper > div > h4")
        if page_404:
            logger.warning(f"Страница не найдена: {edrpo}")
            return False

        # Проверка на 403 Forbidden
        page_403 = await tab.select("h1")
        if page_403:
            text_403 = await tab.get_text("h1")
            if "403 Forbidden" in text_403:
                logger.warning(f"Доступ запрещен (403): {edrpo}")
                return False

        # Проверка на 503 Service Temporarily Unavailable
        page_503 = await tab.select("h1")
        if page_503:
            text_503 = await tab.get_text("h1")
            if "503 Service Temporarily Unavailable" in text_503:
                logger.warning(
                    f"Сервис временно недоступен (503): {edrpo}. Ожидание 10 минут..."
                )
                await asyncio.sleep(600)  # Пауза на 10 минут (600 секунд)
                return False

        logger.info(f"Сохраняем страницу как {file_path}")

        # Получаем HTML-контент страницы
        html_content = await tab.get_content()

        # Создаем файл и сохраняем в него HTML
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        logger.success(f"Страница успешно сохранена: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Ошибка при обработке компании {edrpo} ({url}): {str(e)}")
        return False


async def worker_task(edrpos_chunk, worker_id):
    # Выбираем случайный прокси для этого потока
    proxy = random.choice(PROXY_LIST)
    logger.info(
        f"Запуск рабочего потока #{worker_id} с {len(edrpos_chunk)} задачами, используя прокси: {proxy}"
    )

    browser = None
    try:
        # Инициализируем браузер для этого потока с прокси
        browser = await uc.start(headless=False, proxy_server=proxy)

        # Сначала выполняем вход
        logger.info(f"Поток #{worker_id}: Переходим на страницу логина...")
        await browser.get("https://youcontrol.com.ua/")
        await asyncio.sleep(1)

        # Обрабатываем каждую компанию из чанка
        for i, edrpo in enumerate(edrpos_chunk):
            logger.info(
                f"Поток #{worker_id}: Обработка {i+1}/{len(edrpos_chunk)} - {edrpo}"
            )
            await process_country(browser, edrpo)

    except Exception as e:
        logger.error(f"Ошибка в потоке #{worker_id}: {str(e)}")
    finally:
        # Закрываем браузер
        if browser:
            try:
                await browser.stop()
                logger.info(f"Поток #{worker_id}: Браузер закрыт")
            except Exception as e:
                logger.error(
                    f"Ошибка при закрытии браузера в потоке #{worker_id}: {str(e)}"
                )


# Функция для разделения списка на равные части
def split_into_chunks(lst, n):
    """Разделяет список на n примерно равных частей"""
    chunks = np.array_split(np.array(lst), n)
    return [chunk.tolist() for chunk in chunks]


async def main(edrpos):
    logger.info(f"Запуск с {NUM_THREADS} потоками для обработки {len(edrpos)} компаний")

    # Разделяем список ID компаний на части для каждого потока
    edrpos_chunks = split_into_chunks(edrpos, NUM_THREADS)

    # Создаем и запускаем задачи для каждого потока
    tasks = []
    for i, chunk in enumerate(edrpos_chunks):
        task = asyncio.create_task(worker_task(chunk, i + 1))
        tasks.append(task)

    # Ждем завершения всех задач
    await asyncio.gather(*tasks)

    logger.info("Все потоки завершили работу")


# Функция для чтения ID компаний из CSV файла
def read_companies_from_csv(input_csv_file):
    try:
        df = pd.read_csv(input_csv_file)
        return df["url"].tolist()
    except Exception as e:
        logger.error(f"Ошибка при чтении CSV файла: {e}")
        return []


if __name__ == "__main__":
    # Получаем список ID компаний
    edrpos = read_companies_from_csv(input_csv_file)

    if not edrpos:
        logger.error("Не удалось получить список ID компаний. Проверьте CSV файл.")
        sys.exit(1)

    # Запускаем основную функцию с указанным количеством потоков
    uc.loop().run_until_complete(main(edrpos))
