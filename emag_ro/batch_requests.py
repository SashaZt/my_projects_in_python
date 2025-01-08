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

# URL для Batch Jobs
BATCH_URL = "https://async.scraperapi.com/batchjobs"


class Batch:

    def __init__(
        self,
        api_key,
        html_files_directory,
        csv_output_file,
        # tg_bot,
        job_file,
    ):

        # self.min_count = min_count
        self.api_key = api_key
        self.html_files_directory = html_files_directory
        self.csv_output_file = csv_output_file
        self.job_file = job_file

    def load_jobs_from_file(self):
        """
        Загружает данные задания из JSON-файла.
        """
        if not os.path.exists(self.job_file):
            return None

        try:
            with open(self.job_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Ошибка при загрузке задания из файла: {e}")
            return None

    async def check_all_job_statuses(
        self, session, job_response, max_concurrent_tasks=1000
    ):
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
                            # Сохраняем результат
                            await self.save_result_to_file(job_status)

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
            await self.save_jobs_to_file(remaining_jobs)
            # Пауза в 30 секунд
            logger.info("Пауза на 30 секунд перед следующей проверкой...")
            await asyncio.sleep(30)

            logger.info(
                f"Завершено заданий: {completed_jobs_count}. Осталось: {len(remaining_jobs)}."
            )

        logger.info(
            f"Всего завершенных заданий: {len(job_response) - len(remaining_jobs)} из {len(job_response)}"
        )
        return remaining_jobs

    async def save_jobs_to_file(self, job_response):
        """
        Сохраняет данные задания в JSON-файл асинхронно.
        """
        try:
            async with aiofiles.open(self.job_file, "w", encoding="utf-8") as file:
                await file.write(json.dumps(job_response, indent=4, ensure_ascii=False))
            logger.info(f"Задание сохранено в файл {self.job_file}.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении задания в файл: {e}")

    async def submit_batch_job(self, session, urls):
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
        payload = {"apiKey": self.api_key, "urls": urls}
        try:
            async with session.post(BATCH_URL, json=payload) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error submitting batch job: {e}")
            return []

    # async def fetch_data(self, session, status_url):
    #     """
    #     Извлекает данные из задания, если body отсутствует.

    #     Args:
    #         session (aiohttp.ClientSession): Сессия для выполнения HTTP-запроса.
    #         status_url (str): URL завершенного задания.

    #     Returns:
    #         str or None: Содержимое ответа (body) или None, если запрос не удался.
    #     """
    #     try:
    #         async with session.get(status_url) as response:
    #             response.raise_for_status()
    #             result = await response.json()

    #             # Извлечение body
    #             return result.get("response", {}).get("body", None)
    #     except Exception as e:
    #         logger.error(f"Ошибка извлечения данных из {status_url}: {e}")
    #         return None

    async def scrape_and_save_batch(self, urls, max_concurrent_tasks=1000):
        """
        Создает задания или использует существующие из JOB_FILE и обрабатывает их.

        Args:
            urls (list): Список URL для обработки.
            max_concurrent_tasks (int, optional): Максимальное количество одновременных задач. По умолчанию 100.
        """
        async with aiohttp.ClientSession() as session:
            job_response = self.load_jobs_from_file()
            if not job_response:
                logger.info("Файл JOB_FILE не найден. Создаем новое batch задание.")
                job_response = await self.submit_batch_job(session, urls)
                if not job_response:
                    logger.error("Ошибка при отправке batch-запроса.")
                    return
                await self.save_jobs_to_file(job_response)

            # Проверяем и сохраняем задания
            remaining_jobs = await self.check_all_job_statuses(
                session, job_response, max_concurrent_tasks
            )

            # Удаляем JOB_FILE, если все задания завершены
            if not remaining_jobs:
                if os.path.exists(self.job_file):
                    os.remove(self.job_file)
                logger.info(f"Все задания завершены. Файл {self.job_file} удален.")

    async def save_result_to_file(self, job_result):
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

        filename = self.generate_file_name(url, self.html_files_directory)

        try:
            # Асинхронная запись файла
            async with aiofiles.open(filename, "w", encoding="utf-8") as file:
                await file.write(body)
            logger.info(f"Сохранено: {filename} (Размер: {len(body)} байт)")
        except Exception as e:
            logger.error(f"Ошибка сохранения файла {filename}: {e}")

    def generate_file_name(self, url, output_dir):
        """
        Генерирует имя файла на основе URL в формате pd_<last_part>.
        """
        # Извлечение последней части URL (после последнего "/")
        last_part = url.rstrip("/").split("/")[-1]

        # Формируем имя файла в формате pd_<last_part>.html
        file_name = f"pd_{last_part}.html"

        # Возвращаем полный путь к файлу
        return Path(output_dir) / file_name

    def filter_urls_to_scrape(self, urls, output_dir):
        """
        Фильтрует список URL, оставляя только те, для которых файлы еще не созданы.
        """
        return [
            url for url in urls if not self.generate_file_name(url, output_dir).exists()
        ]

    def clean_completed_jobs(self, job_file, output_dir):
        """
        Удаляет из JOB_FILE задания, чьи файлы уже существуют локально.

        Args:
            job_file (str): Путь к файлу активных заданий.
            output_dir (str): Директория, где хранятся файлы HTML.

        Returns:
            None
        """
        logger.info(job_file)
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
                if not self.generate_file_name(job["url"], output_dir).exists()
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

    def read_csv(self, file_path):
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

    # Рабочий вариант
    def main(self):
        # Очистка JOB_FILE перед обработкой
        self.clean_completed_jobs(self.job_file, self.html_files_directory)
        urls_to_scrape = self.read_csv(self.csv_output_file)
        filtered_urls = self.filter_urls_to_scrape(
            urls_to_scrape, self.html_files_directory
        )

        if not filtered_urls and not os.path.exists(self.job_file):
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
                asyncio.run(self.scrape_and_save_batch(chunk))
