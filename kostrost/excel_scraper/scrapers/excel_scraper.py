import asyncio
import time
from pathlib import Path

import settings
from config.logger import logger
from scrapers.base_scraper import BaseScraper
from scrapers.job_manager import JobManager
from utils.file_utils import extract_urls_from_excel
from utils.url_utils import get_hash_filename_from_url


class ExcelSheetScraper:
    """Класс для скрапинга URL из листов Excel с параллельной обработкой"""

    def __init__(
        self, api_key=None, excel_file_path=None, base_html_dir=None, json_dir=None
    ):
        """
        Инициализация скрапера для листов Excel

        Args:
            api_key: API ключ для ScraperAPI
            excel_file_path: Путь к файлу Excel
            base_html_dir: Базовая директория для сохранения HTML файлов
            json_dir: Директория для хранения JSON файлов с заданиями
        """
        self.api_key = api_key or settings.API_KEY
        self.excel_file_path = excel_file_path or settings.DEFAULT_EXCEL_FILE
        self.base_html_dir = Path(base_html_dir or settings.DEFAULT_HTML_DIR)
        self.json_dir = Path(json_dir or settings.DEFAULT_JSON_DIR)

        # Создаем директории, если они не существуют
        self.base_html_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)

        # Инициализируем базовый скрапер и менеджер заданий
        self.scraper = BaseScraper(api_key=self.api_key)
        self.job_manager = JobManager(self.scraper, json_dir=self.json_dir)

    async def submit_jobs_from_excel(self):
        """
        Отправляет задания на скрапинг для всех URL из Excel с параллельной обработкой

        Returns:
            int: количество отправленных заданий
        """
        start_time = time.time()
        logger.info("Загрузка URL из Excel файла...")

        # Извлекаем URL из Excel файла
        sheet_urls = extract_urls_from_excel(self.excel_file_path, self.base_html_dir)

        total_urls = sum(len(urls) for urls in sheet_urls.values())
        logger.info(f"Найдено всего {total_urls} URL во всех листах")

        # Собираем все URL для параллельной обработки
        urls_to_process = []

        for sheet_name, urls in sheet_urls.items():
            logger.info(f"Подготовка листа '{sheet_name}' ({len(urls)} URL)")

            sheet_name = sheet_name.strip()
            sheet_dir = self.base_html_dir / sheet_name

            for url in urls:
                # Получаем имя файла для URL
                filename = get_hash_filename_from_url(url)
                html_file = sheet_dir / filename

                # Если файл уже существует, пропускаем
                if html_file.exists():
                    logger.debug(f"Файл {html_file} уже существует, пропускаем")
                    continue

                # Проверяем, нет ли уже задания для этого URL
                existing_job, _ = self.job_manager.find_existing_job(url)
                if existing_job:
                    logger.debug(f"Для URL {url} уже есть задание, пропускаем")
                    continue

                # Добавляем URL в список для обработки
                urls_to_process.append((url, html_file, sheet_name))

        if not urls_to_process:
            logger.info("Нет новых URL для обработки или все файлы уже существуют")
            return 0

        # Отправляем задания параллельно
        logger.info(f"Отправка {len(urls_to_process)} заданий параллельно...")
        submitted_count = await self.job_manager.submit_jobs_parallel(urls_to_process)

        execution_time = time.time() - start_time
        logger.info(
            f"Отправка заданий завершена за {execution_time:.2f} сек. Отправлено {submitted_count} из {len(urls_to_process)}"
        )

        return submitted_count

    async def run_initial_check(self):
        """
        Выполняет начальную проверку активных заданий
        """
        active_jobs = self.job_manager.get_active_jobs()

        if active_jobs:
            logger.info(
                f"Найдено {len(active_jobs)} активных заданий. Выполняем начальную проверку..."
            )
            await self.job_manager.process_all_jobs()

    async def main(self):
        """
        Основная функция для запуска процесса скрапинга с параллельной обработкой
        """
        logger.info(
            "Запуск скрапера в режиме непрерывной проверки с параллельной обработкой"
        )

        # Выполняем начальную проверку существующих заданий
        await self.run_initial_check()

        # Отправляем задания из Excel файла параллельно
        total_submitted = await self.submit_jobs_from_excel()

        if total_submitted > 0:
            logger.info(f"Отправлено {total_submitted} новых заданий")

        # Запускаем непрерывную обработку заданий
        await self.job_manager.continuous_process_jobs()
