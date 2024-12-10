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
    exit(1)

# URL для Batch Jobs
BATCH_URL = "https://async.scraperapi.com/batchjobs"

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = current_directory / "html"
json_directory = current_directory / "json"

data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(exist_ok=True, parents=True)
json_directory.mkdir(exist_ok=True, parents=True)
all_urls_page = data_directory / "all_urls.csv"
JOB_FILE = json_directory / "active_jobs.json"  # Файл для хранения задания


# def save_jobs_to_file(job_response):
#     """
#     Сохраняет данные задания в JSON-файл.
#     """
#     try:
#         with open(JOB_FILE, "w", encoding="utf-8") as file:
#             json.dump(job_response, file, indent=4, ensure_ascii=False)
#         logger.info(f"Задание сохранено в файл {JOB_FILE}.")
#     except Exception as e:
#         logger.error(f"Ошибка при сохранении задания в файл: {e}")


def load_jobs_from_file():
    """
    Загружает данные задания из JSON-файла.
    """
    if not os.path.exists(JOB_FILE):
        return None

    try:
        with open(JOB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Ошибка при загрузке задания из файла: {e}")
        return None


# async def check_all_job_statuses(session, job_response, max_concurrent_tasks=100):
#     """
#     Проверяет статусы всех заданий из job_response по блокам.

#     Args:
#         session (aiohttp.ClientSession): Сессия для выполнения HTTP-запросов.
#         job_response (list): Список заданий из JOB_FILE.
#         max_concurrent_tasks (int): Максимальное количество одновременных задач.

#     Returns:
#         list: Список незавершенных заданий.
#     """
#     semaphore = asyncio.Semaphore(max_concurrent_tasks)

#     async def check_status(job):
#         """
#         Проверяет статус конкретного задания и сохраняет завершенные задания.

#         Args:
#             job (dict): Задание для проверки.

#         Returns:
#             dict or None: None, если задание завершено и данные сохранены.
#                           Возвращает job, если задание не завершено.
#         """
#         async with semaphore:
#             try:
#                 logger.info(f"Начало проверки статуса задания: {job['id']}")
#                 async with session.get(job["statusUrl"]) as response:
#                     response.raise_for_status()
#                     job_status = await response.json()

#                     # Лог текущего статуса
#                     current_status = job_status.get("status", "unknown")
#                     logger.info(f"Статус задания {job['id']}: {current_status}")

#                     if current_status == "finished":
#                         logger.info(
#                             f"Задание {job['id']} завершено. Сохраняем результат..."
#                         )

#                         # Сохраняем результат
#                         await save_result_to_file(job_status)
#                         logger.info(f"Результат задания {job['id']} успешно сохранен.")
#                         return None  # Задание завершено

#                     # Если статус не "finished", возвращаем задание для дальнейшей проверки
#                     return job

#             except Exception as e:
#                 logger.error(f"Ошибка проверки статуса задания {job['id']}: {e}")
#                 return job  # Возвращаем задание для повторной проверки

#     remaining_jobs = job_response.copy()
#     completed_jobs_count = 0

#     # Итеративная обработка по блокам
#     while remaining_jobs:
#         current_batch = remaining_jobs[:max_concurrent_tasks]
#         remaining_jobs = remaining_jobs[max_concurrent_tasks:]

#         logger.info(
#             f"Проверка блока из {len(current_batch)} заданий. Осталось {len(remaining_jobs)}."
#         )
#         tasks = [check_status(job) for job in current_batch]
#         results = await asyncio.gather(*tasks)

#         # Обновляем список оставшихся заданий
#         remaining_jobs += [job for job in results if job]
#         completed_jobs_count += len(current_batch) - len(results)

#         logger.info(
#             f"Завершено заданий: {completed_jobs_count}. Осталось: {len(remaining_jobs)}."
#         )

#     logger.info(
#         f"Всего завершенных заданий: {len(job_response) - len(remaining_jobs)} из {len(job_response)}"
#     )
#     return remaining_jobs


# file_lock = asyncio.Lock()


async def check_all_job_statuses(session, job_response, max_concurrent_tasks=500):
    """
    Проверяет статусы всех заданий из job_response и обновляет JOB_FILE после завершения заданий.

    Args:
        session (aiohttp.ClientSession): Сессия для выполнения HTTP-запросов.
        job_response (list): Список заданий из JOB_FILE.
        max_concurrent_tasks (int): Максимальное количество одновременных задач.

    Returns:
        list: Список незавершенных заданий.
    """
    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    remaining_jobs = job_response.copy()  # Копируем, чтобы изменять список

    async def check_status(job):
        """
        Проверяет статус конкретного задания и сохраняет завершенные задания.

        Args:
            job (dict): Задание для проверки.

        Returns:
            dict or None: None, если задание завершено и данные сохранены.
                          Возвращает job, если задание не завершено.
        """
        async with semaphore:
            try:
                # logger.info(f"Начало проверки статуса задания: {job['id']}")
                async with session.get(job["statusUrl"]) as response:
                    response.raise_for_status()
                    job_status = await response.json()

                    # Лог текущего статуса
                    current_status = job_status.get("status", "unknown")
                    # logger.info(f"Статус задания {job['id']}: {current_status}")

                    if current_status == "finished":
                        # logger.info(
                        #     f"Задание {job['id']} завершено. Сохраняем результат..."
                        # )

                        # Сохраняем результат
                        await save_result_to_file(job_status)

                        # logger.info(f"Результат задания {job['id']} успешно сохранен.")
                        return None  # Задание завершено

                    # Если статус не "finished", возвращаем задание для дальнейшей проверки
                    return job

            except Exception as e:
                logger.error(f"Ошибка проверки статуса задания {job['id']}: {e}")
                return job  # Возвращаем задание для повторной проверки

    completed_jobs_count = 0

    # Итеративная обработка по блокам
    while remaining_jobs:
        current_batch = remaining_jobs[:max_concurrent_tasks]
        remaining_jobs = remaining_jobs[max_concurrent_tasks:]

        logger.info(
            f"Проверка блока из {len(current_batch)} заданий. Осталось {len(remaining_jobs)}."
        )
        tasks = [check_status(job) for job in current_batch]
        results = await asyncio.gather(*tasks)

        # Завершенные задания исключаются из remaining_jobs
        remaining_jobs += [job for job in results if job]
        completed_jobs_count += len(current_batch) - len(results)

        # Обновляем JOB_FILE
        await save_jobs_to_file(remaining_jobs)
        # logger.info(
        #     f"Файл {JOB_FILE} обновлен. Осталось {len(remaining_jobs)} заданий."
        # )

        logger.info(
            f"Завершено заданий: {completed_jobs_count}. Осталось: {len(remaining_jobs)}."
        )

    logger.info(
        f"Всего завершенных заданий: {len(job_response) - len(remaining_jobs)} из {len(job_response)}"
    )
    return remaining_jobs


# async def save_jobs_to_file_with_lock(job_response):
#     """
#     Сохраняет данные задания в JSON-файл с использованием asyncio.Lock.
#     """
#     async with file_lock:
#         try:
#             with open(JOB_FILE, "w", encoding="utf-8") as file:
#                 json.dump(job_response, file, indent=4, ensure_ascii=False)
#             logger.info(f"Задание сохранено в файл {JOB_FILE}.")
#         except Exception as e:
#             logger.error(f"Ошибка при сохранении задания в файл: {e}")


async def save_jobs_to_file(job_response):
    """
    Сохраняет данные задания в JSON-файл асинхронно.
    """
    try:
        async with aiofiles.open(JOB_FILE, "w", encoding="utf-8") as file:
            await file.write(json.dumps(job_response, indent=4, ensure_ascii=False))
        logger.info(f"Задание сохранено в файл {JOB_FILE}.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении задания в файл: {e}")


# Рабочий полностью
# async def check_all_job_statuses(session, job_response, max_concurrent_tasks=100):
#     """
#     Проверяет статусы всех заданий из job_response и сохраняет завершенные задания.

#     Args:
#         session (aiohttp.ClientSession): Сессия для выполнения HTTP-запросов.
#         job_response (list): Список заданий из JOB_FILE.
#         max_concurrent_tasks (int): Максимальное количество одновременных задач.

#     Returns:
#         list: Список незавершенных заданий.
#     """
#     semaphore = asyncio.Semaphore(max_concurrent_tasks)

#     async def check_status(job):
#         """
#         Проверяет статус конкретного задания и сохраняет завершенные задания.

#         Args:
#             job (dict): Задание для проверки.

#         Returns:
#             dict or None: None, если задание завершено и данные сохранены.
#                           Возвращает job, если задание не завершено.
#         """
#         async with semaphore:
#             try:
#                 logger.info(f"Начало проверки статуса задания: {job['id']}")
#                 while True:
#                     async with session.get(job["statusUrl"]) as response:
#                         response.raise_for_status()
#                         job_status = await response.json()

#                         # Лог текущего статуса
#                         current_status = job_status.get("status", "unknown")
#                         logger.info(f"Статус задания {job['id']}: {current_status}")

#                         if current_status == "finished":
#                             logger.info(
#                                 f"Задание {job['id']} завершено. Сохраняем результат..."
#                             )

#                             # Сохраняем результат
#                             await save_result_to_file(job_status)
#                             logger.info(
#                                 f"Результат задания {job['id']} успешно сохранен."
#                             )
#                             return None  # Задание завершено, исключаем из оставшихся

#                         # Ждем перед повторной проверкой
#                         await asyncio.sleep(1)

#             except Exception as e:
#                 logger.error(f"Ошибка проверки статуса задания {job['id']}: {e}")
#                 return job  # Возвращаем задание для повторной проверки

#     # Обрабатываем задания параллельно
#     tasks = [check_status(job) for job in job_response]
#     results = await asyncio.gather(*tasks)

#     # Возвращаем только незавершенные задания
#     remaining_jobs = [job for job in results if job]
#     logger.info(
#         f"Всего завершенных заданий: {len(job_response) - len(remaining_jobs)} из {len(job_response)}"
#     )
#     return remaining_jobs


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


async def fetch_data(session, status_url):
    """
    Извлекает данные из задания, если body отсутствует.

    Args:
        session (aiohttp.ClientSession): Сессия для выполнения HTTP-запроса.
        status_url (str): URL завершенного задания.

    Returns:
        str or None: Содержимое ответа (body) или None, если запрос не удался.
    """
    try:
        async with session.get(status_url) as response:
            response.raise_for_status()
            result = await response.json()

            # Извлечение body
            return result.get("response", {}).get("body", None)
    except Exception as e:
        logger.error(f"Ошибка извлечения данных из {status_url}: {e}")
        return None


async def scrape_and_save_batch(urls, max_concurrent_tasks=500):
    """
    Создает задания или использует существующие из JOB_FILE и обрабатывает их.

    Args:
        urls (list): Список URL для обработки.
        max_concurrent_tasks (int, optional): Максимальное количество одновременных задач. По умолчанию 100.
    """
    async with aiohttp.ClientSession() as session:
        job_response = load_jobs_from_file()
        if not job_response:
            logger.info("Файл JOB_FILE не найден. Создаем новое batch задание.")
            job_response = await submit_batch_job(session, urls)
            if not job_response:
                logger.error("Ошибка при отправке batch-запроса.")
                return
            await save_jobs_to_file(job_response)

        # Проверяем и сохраняем задания
        remaining_jobs = await check_all_job_statuses(
            session, job_response, max_concurrent_tasks
        )

        # Удаляем JOB_FILE, если все задания завершены
        if not remaining_jobs:
            if os.path.exists(JOB_FILE):
                os.remove(JOB_FILE)
            logger.info(f"Все задания завершены. Файл {JOB_FILE} удален.")


# async def scrape_and_save_batch(urls, max_concurrent_tasks=100):
#     async with aiohttp.ClientSession() as session:
#         job_response = load_jobs_from_file()
#         if not job_response:
#             logger.info("Файл JOB_FILE не найден. Создаем новое batch задание.")
#             job_response = await submit_batch_job(session, urls)
#             if not job_response:
#                 logger.error("Ошибка при отправке batch-запроса.")
#                 return
#             save_jobs_to_file(job_response)

#         # Проверяем и сохраняем задания
#         remaining_jobs = await check_all_job_statuses(
#             session, job_response, max_concurrent_tasks
#         )

#         # Обновляем JOB_FILE
#         if remaining_jobs:
#             save_jobs_to_file(remaining_jobs)
#             logger.info(
#                 f"Файл {JOB_FILE} обновлен. Осталось {len(remaining_jobs)} заданий."
#             )
#         else:
#             if os.path.exists(JOB_FILE):
#                 os.remove(JOB_FILE)
#             logger.info(f"Все задания завершены. Файл {JOB_FILE} удален.")


# РАБОЧИЙ полностью
# async def scrape_and_save_batch(urls, max_concurrent_tasks=100):
#     """
#     Создает задания или использует существующие из JOB_FILE и обрабатывает их.

#     Args:
#         urls (list): Список URL для обработки.
#         max_concurrent_tasks (int, optional): Максимальное количество одновременных задач. По умолчанию 100.
#     """
#     async with aiohttp.ClientSession() as session:
#         job_response = load_jobs_from_file()
#         if job_response:
#             logger.info(f"Загружено {len(job_response)} заданий из файла {JOB_FILE}.")
#         else:
#             logger.info("Файл JOB_FILE не найден. Создаем новое batch задание.")
#             job_response = await submit_batch_job(session, urls)
#             if not job_response:
#                 logger.error("Ошибка при отправке batch-запроса.")
#                 return
#             save_jobs_to_file(job_response)

#         # Проверяем и сохраняем задания
#         remaining_jobs = await check_all_job_statuses(
#             session, job_response, max_concurrent_tasks
#         )

#         # Обновляем JOB_FILE
#         if remaining_jobs:
#             save_jobs_to_file(remaining_jobs)
#             logger.info(
#                 f"Файл {JOB_FILE} обновлен. Осталось {len(remaining_jobs)} заданий."
#             )
#         else:
#             if os.path.exists(JOB_FILE):
#                 os.remove(JOB_FILE)
#             logger.info(f"Все задания завершены. Файл {JOB_FILE} удален.")


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


def generate_file_name(url, output_dir):
    """
    Генерирует имя файла на основе URL.
    """
    url_parts = url.split("/")
    last_part = url_parts[-1].split("?")
    base_name = "_".join(part.replace("-", "_") for part in url_parts[-3:-1] if part)
    file_name = f"{base_name}_{last_part[0].replace('-', '_')}.html"
    return Path(output_dir) / file_name


def filter_urls_to_scrape(urls, output_dir):
    """
    Фильтрует список URL, оставляя только те, для которых файлы еще не созданы.
    """
    return [url for url in urls if not generate_file_name(url, output_dir).exists()]


def clean_completed_jobs(job_file, output_dir):
    """
    Удаляет из JOB_FILE задания, чьи файлы уже существуют локально.

    Args:
        job_file (str): Путь к файлу активных заданий.
        output_dir (str): Директория, где хранятся файлы HTML.

    Returns:
        None
    """
    if not os.path.exists(job_file):
        logger.info(f"Файл {job_file} не найден. Очистка не требуется.")
        return

    try:
        # Загружаем задания из JOB_FILE
        with open(job_file, "r", encoding="utf-8") as file:
            jobs = json.load(file)

        # Оставляем только те задания, чьи файлы ещё не существуют
        remaining_jobs = [
            job
            for job in jobs
            if not generate_file_name(job["url"], output_dir).exists()
        ]

        # Если ничего не изменилось, не обновляем файл
        if len(remaining_jobs) == len(jobs):
            logger.info("Очистка не требовалась. Все задания актуальны.")
            return

        # Сохраняем обновлённый JOB_FILE
        with open(job_file, "w", encoding="utf-8") as file:
            json.dump(remaining_jobs, file, indent=4, ensure_ascii=False)

        logger.info(
            f"Очистка завершена. Удалено {len(jobs) - len(remaining_jobs)} заданий."
        )
    except Exception as e:
        logger.error(f"Ошибка при очистке JOB_FILE: {e}")


def read_csv(file_path):
    """
    Читает URL из CSV-файла.
    """
    if not os.path.exists(file_path):
        logger.error(f"Файл CSV не найден: {file_path}")
        return []

    try:
        data = pd.read_csv(file_path)
        return data.get("url", []).tolist()
    except Exception as e:
        logger.error(f"Ошибка при чтении CSV: {e}")
        return []


# РАбочий
# if __name__ == "__main__":
#     # Очистка JOB_FILE перед обработкой
#     clean_completed_jobs(JOB_FILE, html_directory)
#     urls_to_scrape = read_csv(all_urls_page)
#     filtered_urls = filter_urls_to_scrape(urls_to_scrape, html_directory)

#     if not filtered_urls and not os.path.exists(JOB_FILE):
#         logger.info("Нет URL для обработки и активных заданий.")
#     else:
#         asyncio.run(scrape_and_save_batch(filtered_urls))


if __name__ == "__main__":
    # Очистка JOB_FILE перед обработкой
    clean_completed_jobs(JOB_FILE, html_directory)
    urls_to_scrape = read_csv(all_urls_page)
    filtered_urls = filter_urls_to_scrape(urls_to_scrape, html_directory)

    if not filtered_urls and not os.path.exists(JOB_FILE):
        logger.info("Нет URL для обработки и активных заданий.")
    else:
        # Разбиваем filtered_urls на блоки по 50,000
        chunk_size = 40000
        chunks = [
            filtered_urls[i : i + chunk_size]
            for i in range(0, len(filtered_urls), chunk_size)
        ]

        for i, chunk in enumerate(chunks, start=1):
            logger.info(f"Обработка блока {i}/{len(chunks)} с {len(chunk)} URL.")
            asyncio.run(scrape_and_save_batch(chunk))
