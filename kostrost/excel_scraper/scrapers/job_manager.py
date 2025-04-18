import asyncio
import time
from pathlib import Path

import settings
from config.logger import logger
from utils.file_utils import (
    delete_job_file,
    load_job_info,
    save_html_content,
    save_job_info,
)


class JobManager:
    """Класс для управления заданиями скрапинга с параллельной обработкой"""

    def __init__(self, scraper, json_dir="json_jobs"):
        """
        Инициализация менеджера заданий

        Args:
            scraper: экземпляр скрапера
            json_dir: директория для хранения информации о заданиях
        """
        self.scraper = scraper
        self.json_dir = Path(json_dir)
        self.json_dir.mkdir(parents=True, exist_ok=True)

        # Настройки параллельной обработки
        self.max_parallel_checks = settings.MAX_PARALLEL_CHECKS
        self.max_parallel_submits = settings.MAX_PARALLEL_SUBMITS
        self.check_batch_size = settings.CHECK_BATCH_SIZE

    def find_existing_job(self, url):
        """
        Проверяет, есть ли уже задание для указанного URL

        Args:
            url: URL страницы

        Returns:
            tuple: (job_info, json_file_path) или (None, None) если задание не найдено
        """
        for json_file in self.json_dir.glob("*.json"):
            try:
                job_info = load_job_info(json_file)

                if job_info and job_info.get("url") == url:
                    return job_info, json_file
            except Exception as e:
                logger.error(f"Ошибка при чтении файла задания {json_file}: {str(e)}")

        return None, None

    def get_all_jobs(self):
        """
        Получает все текущие задания

        Returns:
            list: список кортежей (job_info, json_file)
        """
        jobs = []

        for json_file in self.json_dir.glob("*.json"):
            try:
                job_info = load_job_info(json_file)

                if job_info:
                    jobs.append((job_info, json_file))
            except Exception as e:
                logger.error(f"Ошибка при чтении файла задания {json_file}: {str(e)}")

        return jobs

    def get_active_jobs(self):
        """
        Получает все активные задания (не завершенные)

        Returns:
            list: список кортежей (job_info, json_file)
        """
        active_jobs = []

        for job_info, json_file in self.get_all_jobs():
            status = job_info.get("status")

            if status != "finished" and status != "failed":
                active_jobs.append((job_info, json_file))

        return active_jobs

    async def submit_job(self, url, html_file, sheet_name=None):
        """
        Отправляет задание на скрапинг

        Args:
            url: URL страницы
            html_file: путь для сохранения HTML
            sheet_name: имя листа Excel (опционально)

        Returns:
            tuple: (job_info, success) - информация о задании и флаг успеха
        """
        # Проверяем, нет ли уже задания для этого URL
        existing_job, json_file = self.find_existing_job(url)

        if existing_job:
            logger.info(f"Для URL {url} уже есть задание {existing_job.get('id')}")

            # Обновляем информацию о файле HTML, если её нет
            if not existing_job.get("html_file"):
                existing_job["html_file"] = str(html_file)
                save_job_info(self.json_dir, existing_job["id"], existing_job)

            return existing_job, True

        # Отправляем новое задание
        job_info = self.scraper.submit_job(url)

        if job_info:
            # Добавляем дополнительную информацию
            job_info["html_file"] = str(html_file)

            if sheet_name:
                job_info["sheet_name"] = sheet_name

            # Сохраняем информацию о задании
            save_job_info(self.json_dir, job_info["id"], job_info)

            return job_info, True

        return None, False

    async def check_job_with_retries(self, job_info):
        """
        Проверяет задание с несколькими попытками

        Args:
            job_info: Информация о задании

        Returns:
            Tuple (status, html_content, job_completed)
        """
        for attempt in range(settings.MAX_JOB_CHECK_ATTEMPTS):
            status, html_content = self.scraper.check_job_status(job_info)

            if status == "finished" and html_content:
                return status, html_content, True
            elif status == "failed":
                return status, None, True  # Задание завершено с ошибкой
            elif status == "running" or status == "unknown" or status == "error":
                # Задание еще выполняется или произошла ошибка проверки
                if attempt < settings.MAX_JOB_CHECK_ATTEMPTS - 1:
                    logger.debug(
                        f"Ожидание {settings.JOB_CHECK_INTERVAL} секунд перед следующей попыткой..."
                    )
                    await asyncio.sleep(settings.JOB_CHECK_INTERVAL)
                continue

        # Если мы дошли сюда, значит все попытки исчерпаны
        logger.warning(
            f"Превышено количество попыток проверки для задания {job_info.get('id')}"
        )
        return "timeout", None, False  # Задание не завершено, но попытки исчерпаны

    async def process_job(self, job_info, json_file):
        """
        Обрабатывает одно задание

        Args:
            job_info: информация о задании
            json_file: путь к файлу задания

        Returns:
            bool: True если задание обработано (успешно или неуспешно), иначе False
        """
        job_id = job_info.get("id")
        url = job_info.get("url")
        html_file_path = job_info.get("html_file")

        if not html_file_path:
            logger.error(f"Нет пути к HTML для задания {job_id}")
            return False

        html_file = Path(html_file_path)

        # Если файл уже существует, удаляем задание
        if html_file.exists():
            try:
                delete_job_file(json_file)
                logger.info(f"HTML уже существует, задание {job_id} удалено")
                return True
            except Exception as e:
                logger.error(f"Ошибка при удалении файла задания: {str(e)}")
                return False

        # Проверяем статус задания с несколькими попытками
        status, html_content, job_completed = await self.check_job_with_retries(
            job_info
        )

        if status == "finished" and html_content:
            # Сохраняем HTML
            if save_html_content(html_file, html_content):
                # Удаляем файл задания
                delete_job_file(json_file)
                logger.info(f"Задание {job_id} успешно завершено и удалено")
                return True

        elif status == "failed" and job_completed:
            # Обновляем статус задания
            job_info["status"] = "failed"
            save_job_info(self.json_dir, job_id, job_info)
            logger.info(f"Статус задания {job_id} обновлен на 'failed'")
            return True

        return False

    async def process_job_batch(self, jobs_batch):
        """
        Обрабатывает пакет заданий параллельно

        Args:
            jobs_batch: список кортежей (job_info, json_file)

        Returns:
            int: количество обработанных заданий
        """
        if not jobs_batch:
            return 0

        # Создаем задачи для параллельной обработки
        tasks = [
            self.process_job(job_info, json_file) for job_info, json_file in jobs_batch
        ]

        # Запускаем задачи параллельно и ждем их завершения
        results = await asyncio.gather(*tasks)

        # Подсчитываем количество успешно обработанных заданий
        processed_count = sum(1 for result in results if result)

        return processed_count

    async def process_all_jobs(self):
        """
        Обрабатывает все активные задания с параллельной обработкой

        Returns:
            tuple: (processed_count, total_count)
        """
        active_jobs = self.get_active_jobs()

        if not active_jobs:
            logger.info("Нет активных заданий для обработки")
            return 0, 0

        total_count = len(active_jobs)
        logger.info(
            f"Обработка {total_count} активных заданий с параллельной обработкой..."
        )

        processed_count = 0

        # Разбиваем задания на пакеты для параллельной обработки
        for i in range(0, total_count, self.check_batch_size):
            batch = active_jobs[i : i + self.check_batch_size]
            logger.info(
                f"Обработка пакета {i//self.check_batch_size + 1}/{(total_count + self.check_batch_size - 1)//self.check_batch_size} (размер: {len(batch)})"
            )

            batch_processed = await self.process_job_batch(batch)
            processed_count += batch_processed

            # Небольшая пауза между пакетами, чтобы не перегружать API
            if i + self.check_batch_size < total_count:
                await asyncio.sleep(1)

        logger.info(f"Обработано заданий: {processed_count}/{total_count}")
        return processed_count, total_count

    async def submit_jobs_parallel(self, urls_info):
        """
        Отправляет задания параллельно

        Args:
            urls_info: список кортежей (url, html_file, sheet_name)

        Returns:
            int: количество отправленных заданий
        """
        if not urls_info:
            return 0

        logger.info(f"Параллельная отправка {len(urls_info)} заданий...")

        # Создаем семафор для ограничения количества параллельных отправок
        semaphore = asyncio.Semaphore(self.max_parallel_submits)

        async def submit_with_semaphore(url, html_file, sheet_name):
            async with semaphore:
                return await self.submit_job(url, html_file, sheet_name)

        # Создаем задачи для параллельной отправки
        tasks = [
            submit_with_semaphore(url, html_file, sheet_name)
            for url, html_file, sheet_name in urls_info
        ]

        # Запускаем задачи параллельно и ждем их завершения
        results = await asyncio.gather(*tasks)

        # Подсчитываем количество успешно отправленных заданий
        submitted_count = sum(1 for job_info, success in results if success)

        logger.info(f"Успешно отправлено {submitted_count}/{len(urls_info)} заданий")
        return submitted_count

    async def continuous_process_jobs(self):
        """
        Непрерывно обрабатывает задания в цикле с параллельной обработкой
        """
        while True:
            start_time = time.time()

            # Обрабатываем все активные задания параллельно
            processed_count, total_count = await self.process_all_jobs()

            # Вычисляем время выполнения
            execution_time = time.time() - start_time

            # Если все задания обработаны или нет активных заданий
            if total_count == 0 or processed_count == total_count:
                logger.info(
                    f"Все задания обработаны за {execution_time:.2f} сек. Ожидание {settings.CHECK_CYCLE_INTERVAL} секунд..."
                )
            else:
                logger.info(
                    f"Обработка заняла {execution_time:.2f} сек. Остались необработанные задания. Ожидание {settings.CHECK_CYCLE_INTERVAL} секунд..."
                )

            # Пауза перед следующим циклом проверок
            await asyncio.sleep(settings.CHECK_CYCLE_INTERVAL)
