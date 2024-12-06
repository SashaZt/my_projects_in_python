# Рабочий код для сайта scraperapi асинхронное скачивание файлов через сервис
import asyncio
import json
import os
from pathlib import Path

import aiofiles
import aiohttp
import pandas as pd
from configuration.logger_setup import logger
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), "configuration", ".env")

if not os.path.exists(env_path):
    logger.error(f"Файл .env не найден: {env_path}")
    exit(1)
load_dotenv(env_path)

# Ваш ScraperAPI ключ
SCRAPERAPI_KEY = os.getenv("API_KEY")
if not SCRAPERAPI_KEY:
    logger.error("API_KEY не определен в файле .env.")
    exit(1)  # Завершаем программу, если ключ отсутствует


# URL для Batch Jobs
BATCH_URL = "https://async.scraperapi.com/batchjobs"


# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml_file"
html_directory = current_directory / "html"
json_directory = current_directory / "json"
xml_files_directory = current_directory / "xml_files"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(exist_ok=True, parents=True)
json_directory.mkdir(exist_ok=True, parents=True)
xml_directory.mkdir(exist_ok=True, parents=True)
xml_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
all_urls_page = data_directory / "all_urls.csv"
JOB_FILE = json_directory / "active_jobs.json"  # Файл для хранения задания


def save_jobs_to_file(job_response):
    """
    Сохраняет данные задания в JSON-файл.

    Args:
        job_response (list): Список заданий, содержащий данные о статусе и URL.

    Raises:
        Exception: Логирует ошибку, если файл не удалось сохранить.
    """
    try:
        with open(JOB_FILE, "w", encoding="utf-8") as file:
            json.dump(job_response, file, indent=4, ensure_ascii=False)
        logger.info(f"Задание сохранено в файл {JOB_FILE}.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении задания в файл: {e}")


def load_jobs_from_file():
    """
    Загружает данные задания из JSON-файла.

    Returns:
        list or None: Список заданий, если файл существует и успешно прочитан.
                      None, если файл отсутствует или произошла ошибка при чтении.
    """
    if not os.path.exists(JOB_FILE):
        return None

    try:
        with open(JOB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Ошибка при загрузке задания из файла: {e}")
        return None


async def submit_batch_job(session, urls):
    """
    Создает batch job для множества URL-адресов.

    Args:
        session (aiohttp.ClientSession): Сессия для выполнения HTTP-запроса.
        urls (list): Список URL для обработки.

    Returns:
        list: Ответ API с данными о созданных заданиях.
              Пустой список, если произошла ошибка.

    Raises:
        Exception: Логирует ошибку при неудачной попытке создания batch job.
    """
    payload = {"apiKey": SCRAPERAPI_KEY, "urls": urls}
    try:
        async with session.post(BATCH_URL, json=payload) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        logger.error(f"Error submitting batch job: {e}")
        return []


async def check_job_status(session, status_url):
    """
    Проверяет статус одного задания по статусу URL.

    Args:
        session (aiohttp.ClientSession): Сессия для выполнения HTTP-запроса.
        status_url (str): URL для проверки статуса задания.

    Returns:
        dict or None: Данные о завершенном задании, если статус "finished".
                      None, если произошла ошибка при проверке статуса.

    Raises:
        Exception: Логирует ошибку при неудачной проверке статуса.
    """
    while True:
        try:
            async with session.get(status_url) as response:
                response.raise_for_status()
                job_status = await response.json()
                if job_status["status"] == "finished":
                    return job_status
                await asyncio.sleep(1)  # Ждем перед повторной проверкой
        except Exception as e:
            logger.error(f"Error checking job status: {e}")
            return None


async def save_result_to_file(job_result):
    """
    Сохраняет результат задания в HTML-файл.

    Args:
        job_result (dict): Данные задания, включающие URL и содержимое HTML.

    Note:
        Если `body` в `job_result` отсутствует или не является строкой, файл не сохраняется.
    """
    url = job_result["url"]
    body = job_result.get("response", {}).get("body", "")

    # Проверяем, является ли body строкой
    if not isinstance(body, str) or not body.strip():
        logger.warning(
            f"Пропускаем сохранение для URL {url}, так как body не является строкой или пуст."
        )
        return

    filename = generate_file_name(url, html_directory)

    try:
        # Асинхронная запись файла
        async with aiofiles.open(filename, "w", encoding="utf-8") as file:
            await file.write(body)
        logger.info(f"Сохранено: {filename} (Размер: {len(body)} байт)")
    except Exception as e:
        logger.error(f"Ошибка сохранения файла {filename}: {e}")


# РАБОЧИЙ КОД
# async def save_result_to_file(job_result):
#     """
#     Сохраняет результат задания в HTML-файл.
#     """
#     url = job_result["url"]
#     body = job_result.get("response", {}).get("body", "")
#     if body:
#         filename = generate_file_name(url, html_directory)
#         try:
#             with open(filename, "w", encoding="utf-8") as file:
#                 file.write(body)
#             logger.info(f"Сохранено: {filename}")
#         except Exception as e:
#             logger.error(f"Ошибка сохранения файла {filename}: {e}")

# ТОЖЕ РАБОЧИЙ КОД
# async def save_result_to_file(job_result):
#     """
#     Сохраняет результат задания в HTML-файл.

#     Args:
#         job_result (dict): Данные задания, включающие URL и содержимое HTML.

#     Raises:
#         Exception: Логирует ошибку, если файл не удалось сохранить.

#     Note:
#         Если `body` в `job_result` отсутствует или не является строкой, файл не сохраняется.
#     """
#     url = job_result["url"]
#     body = job_result.get("response", {}).get("body", "")

#     # Проверяем, является ли body строкой
#     if not isinstance(body, str):
#         logger.warning(
#             f"Пропускаем сохранение для URL {url}, так как body не является строкой."
#         )
#         return

#     filename = generate_file_name(url, html_directory)
#     try:
#         with open(filename, "w", encoding="utf-8") as file:
#             file.write(body)
#         logger.info(f"Сохранено: {filename}")
#     except Exception as e:
#         logger.error(f"Ошибка сохранения файла {filename}: {e}")


# РАБОЧИЙ КОД
# async def scrape_and_save_batch(urls, max_concurrent_tasks=100):
#     """
#     Основная функция для выполнения batch scraping и сохранения результатов.
#     """
#     async with aiohttp.ClientSession() as session:
#         logger.info(f"Отправка {len(urls)} URL для обработки.")
#         job_response = await submit_batch_job(session, urls)
#         if not job_response:
#             logger.error("Ошибка при отправке batch-запроса.")
#             return

#         logger.info(f"Создано {len(job_response)} заданий для обработки.")

#         semaphore = asyncio.Semaphore(max_concurrent_tasks)

#         async def process_job(job):
#             async with semaphore:
#                 result = await check_job_status(session, job["statusUrl"])
#                 if result and result["status"] == "finished":
#                     await save_result_to_file(result)
#                 else:
#                     logger.warning(
#                         f"Задание {job['id']} завершено с некорректным статусом."
#                     )

#         tasks = [process_job(job) for job in job_response]
#         await asyncio.gather(*tasks)
#         logger.info("Обработка batch-запроса завершена.")


async def scrape_and_save_batch(urls, max_concurrent_tasks=200):
    """
    Основная функция для выполнения batch scraping и сохранения результатов.

    Args:
        urls (list): Список URL для обработки.
        max_concurrent_tasks (int, optional): Максимальное количество одновременных задач. По умолчанию 100.

    Returns:
        None: Все результаты сохраняются в локальные файлы.

    Raises:
        Exception: Логирует ошибки при создании заданий, проверке статусов или сохранении файлов.

    Note:
        Сохраняет активное задание в файл `active_jobs.json` для повторного использования.
    """
    async with aiohttp.ClientSession() as session:
        # Загружаем сохраненное задание, если оно есть
        job_response = load_jobs_from_file()
        if job_response:
            logger.info(f"Загружено существующее задание из файла {JOB_FILE}.")
        else:
            # Создаем новое задание, если сохраненного нет
            job_response = await submit_batch_job(session, urls)
            if not job_response:
                logger.error("Ошибка при отправке batch-запроса.")
                return
            save_jobs_to_file(
                job_response
            )  # Сохраняем задание для повторного использования

        logger.info(f"Обработка {len(job_response)} заданий.")

        semaphore = asyncio.Semaphore(max_concurrent_tasks)

        async def process_job(job):
            """
            Обрабатывает одно задание: проверяет статус и сохраняет результат.

            Args:
                job (dict): Задание, включающее ID и statusUrl.
            """
            async with semaphore:
                logger.info(
                    f"Начало обработки задания: {job['id']} (URL: {job['statusUrl']})"
                )
                try:
                    result = await check_job_status(session, job["statusUrl"])
                    if result and result["status"] == "finished":
                        logger.info(
                            f"Задание {job['id']} завершено. Сохраняем результат..."
                        )
                        await save_result_to_file(result)
                        logger.info(f"Результат задания {job['id']} успешно сохранен.")
                    else:
                        logger.warning(
                            f"Задание {job['id']} завершено с некорректным статусом: {result.get('status', 'unknown')}"
                        )
                except Exception as e:
                    logger.error(f"Ошибка при обработке задания {job['id']}: {e}")

        tasks = [process_job(job) for job in job_response]
        await asyncio.gather(*tasks)

        # Очистка сохраненного задания после завершения
        if os.path.exists(JOB_FILE):
            os.remove(JOB_FILE)
        logger.info("Обработка batch-запроса завершена.")


def generate_file_name(url, output_dir):
    """
    Генерирует имя файла на основе URL.
    """
    url_parts = url.split("/")
    last_part = url_parts[-1].split("?")

    # Получаем значимые части пути
    base_name = "_".join(part.replace("-", "_") for part in url_parts[-3:-1] if part)
    # Добавляем последний сегмент (без параметров)
    file_name = f"{base_name}_{last_part[0].replace('-', '_')}.html"

    # Создаем полный путь к файлу
    html_company = Path(output_dir) / file_name
    return html_company


def is_file_already_exists(url, output_dir):
    """
    Проверяет, существует ли файл для данного URL.
    """
    file_path = generate_file_name(url, output_dir)
    return file_path.exists()


def filter_urls_to_scrape(urls, output_dir):
    """
    Фильтрует список URL, оставляя только те, для которых файлы еще не созданы.
    """
    logger.info("Фильтрация URL на основе существующих файлов...")
    filtered_urls = [url for url in urls if not is_file_already_exists(url, output_dir)]
    logger.info(
        f"{len(urls) - len(filtered_urls)} URL пропущены, так как файлы уже существуют."
    )
    return filtered_urls


def read_csv(file_path):
    """
    Читает URL из CSV-файла.
    """
    if not os.path.exists(file_path):
        logger.error(f"Файл CSV не найден: {file_path}")
        return []

    try:
        data = pd.read_csv(file_path)
        if "url" not in data.columns:
            logger.error("CSV не содержит обязательного столбца 'url'. Проверьте файл.")
            return []
        return data["url"].tolist()
    except Exception as e:
        logger.error(f"Ошибка при чтении CSV: {e}")
        return []


if __name__ == "__main__":

    # Чтение всех URL из CSV
    urls_to_scrape = read_csv(all_urls_page)

    if not urls_to_scrape:
        logger.info("Файл CSV пуст или отсутствуют URL.")
    else:
        # Фильтруем URL, исключая те, для которых уже есть файлы
        filtered_urls = filter_urls_to_scrape(urls_to_scrape, html_directory)

        if not filtered_urls:
            logger.info("Все файлы уже существуют. Нечего обрабатывать.")
        else:
            logger.info(
                f"Будет обработано {len(filtered_urls)} URL из {len(urls_to_scrape)}."
            )
            asyncio.run(scrape_and_save_batch(filtered_urls))
