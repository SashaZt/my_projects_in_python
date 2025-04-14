import asyncio
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests
from config.logger import logger

current_directory = Path.cwd()
config_directory = current_directory / "config"
config_file = config_directory / "config.json"
excel_file = "thomann.xlsx"


def get_config():
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


config = get_config()
API_KEY = config["scraperapi"]["api_key"]


class ExcelSheetScraper:
    def __init__(
        self, api_key, excel_file_path, base_html_dir="html_pages", json_dir="json_jobs"
    ):
        """
        Инициализация скрапера для листов Excel

        Args:
            api_key: API ключ для ScraperAPI
            excel_file_path: Путь к файлу Excel
            base_html_dir: Базовая директория для сохранения HTML файлов
            json_dir: Директория для хранения JSON файлов с заданиями
        """
        self.api_key = api_key
        self.excel_file_path = excel_file_path
        self.base_html_dir = Path(base_html_dir)
        self.json_dir = Path(json_dir)

        # Создаем директории, если они не существуют
        self.base_html_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)

    def extract_urls_from_excel(self):
        """
        Извлекает URL из всех листов Excel файла

        Returns:
            Dictionary mapping sheet names to lists of URLs
        """
        sheet_urls = {}

        # Читаем Excel файл
        xl = pd.ExcelFile(self.excel_file_path)
        sheet_names = xl.sheet_names

        for sheet_name in sheet_names:
            # Создаем директорию для листа
            sheet_name = sheet_name.strip()
            sheet_dir = self.base_html_dir / sheet_name

            sheet_dir.mkdir(exist_ok=True)

            # Читаем только столбец A из листа
            df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name, usecols=[0])

            # Извлекаем URL из столбца A, исключая пустые значения
            urls = [str(value) for value in df.iloc[:, 0].dropna()]

            if urls:
                sheet_urls[sheet_name] = urls
                logger.info(f"Найдено {len(urls)} URL в листе '{sheet_name}'")
            else:
                logger.warning(f"В листе '{sheet_name}' не найдено URL")

        return sheet_urls

    def get_filename_from_url(self, url):
        """
        Формирует имя файла из URL

        Args:
            url: URL страницы

        Returns:
            Имя файла для сохранения HTML
        """
        # Очищаем URL от протокола и параметров
        clean_url = url.strip()

        # Создаем безопасное имя файла, заменяя все небуквенные символы на _
        filename = re.sub(r"[^a-zA-Z0-9]", "_", clean_url)

        # Ограничиваем длину имени файла
        if len(filename) > 100:
            filename = filename[:100]

        return f"{filename}.html"

    def get_domain_filename_from_url(self, url):
        """
        Создает имя файла на основе домена и пути URL

        Args:
            url: URL страницы

        Returns:
            Имя файла для сохранения HTML в формате domain_path.html
        """
        try:
            # Парсинг URL
            parsed_url = urllib.parse.urlparse(url)

            # Получение домена без www
            domain = parsed_url.netloc.replace("www.", "")

            # Получение пути без ведущего слеша и замена всех / на _
            path = parsed_url.path.strip("/")
            if path:
                path = path.replace("/", "_")
                filename = f"{domain}_{path}.html"
            else:
                filename = f"{domain}.html"

            # Замена всех небуквенных символов на _
            filename = re.sub(r"[^\w\.-]", "_", filename)

            # Ограничение длины имени файла
            if len(filename) > 120:
                filename = filename[:120]

            return filename
        except Exception as e:
            logger.error(f"Ошибка при создании имени файла из URL {url}: {str(e)}")
            # Возвращаем запасной вариант имени файла
            return self.get_filename_from_url(url)

    def check_existing_job_status(self, job_info):
        """
        Проверяет статус существующего задания

        Args:
            job_info: Информация о задании

        Returns:
            Tuple (status_code, html_content):
                - status_code: 'finished', 'running', 'failed' или None
                - html_content: HTML-контент (если задание завершено) или None
        """
        job_id = job_info.get("id")
        if not job_id:
            return None, None

        url = job_info.get("url")
        status_url = f"https://async.scraperapi.com/jobs/{job_id}"

        logger.info(f"Проверка статуса задания {job_id} для URL {url}")

        max_attempts = 2
        wait_time = 2  # секунд

        for attempt in range(max_attempts):
            try:
                # Проверяем статус задания
                status_response = requests.get(
                    status_url, params={"apiKey": self.api_key}, timeout=30
                )

                if status_response.status_code != 200:
                    logger.error(
                        f"Ошибка при проверке статуса: {status_response.status_code}"
                    )
                    time.sleep(wait_time)
                    continue

                status_data = status_response.json()
                job_status = status_data.get("status")

                logger.info(
                    f"Статус задания {job_id}: {job_status} (попытка {attempt+1}/{max_attempts})"
                )

                if job_status == "finished":
                    # Получаем результат
                    result_url = f"{status_url}/result"
                    result_response = requests.get(
                        result_url, params={"apiKey": self.api_key}, timeout=60
                    )

                    if result_response.status_code == 200:
                        result_data = result_response.json()

                        # Получаем HTML-контент
                        html_content = None

                        # Проверяем структуру ответа
                        if isinstance(result_data, list):
                            # Если результат - список (для batch-запросов)
                            for item in result_data:
                                if item.get("url") == url:
                                    html_content = item.get("response", {}).get("body")
                                    break
                        else:
                            # Проверяем наличие response и body в ответе
                            if (
                                "response" in result_data
                                and "body" in result_data["response"]
                            ):
                                html_content = result_data["response"]["body"]
                            # Иногда тело может быть закодировано в base64
                            elif (
                                "response" in result_data
                                and "base64EncodedBody" in result_data["response"]
                            ):
                                import base64

                                encoded_body = result_data["response"][
                                    "base64EncodedBody"
                                ]
                                html_content = base64.b64decode(encoded_body).decode(
                                    "utf-8", errors="replace"
                                )

                        if html_content:
                            return "finished", html_content
                        else:
                            logger.error(f"HTML-контент не найден для URL {url}")
                            logger.debug(f"Структура ответа: {result_data}")
                            return "failed", None
                    elif result_response.status_code == 404:
                        # Если задание завершено, но результат не найден, пробуем получить HTML из статуса
                        logger.warning(
                            f"Результат задания {job_id} не найден (404), пробуем извлечь из статуса"
                        )

                        # Проверяем, есть ли response в данных статуса
                        if "response" in status_data:
                            if "body" in status_data["response"]:
                                html_content = status_data["response"]["body"]
                                return "finished", html_content
                            elif "base64EncodedBody" in status_data["response"]:
                                import base64

                                encoded_body = status_data["response"][
                                    "base64EncodedBody"
                                ]
                                html_content = base64.b64decode(encoded_body).decode(
                                    "utf-8", errors="replace"
                                )
                                return "finished", html_content

                        logger.error(
                            f"Не удалось извлечь HTML из статуса задания {job_id}"
                        )
                        return "failed", None
                    else:
                        logger.error(
                            f"Ошибка при получении результата: {result_response.status_code}"
                        )
                        return "failed", None

                elif job_status == "failed":
                    error = status_data.get("error") or "Неизвестная ошибка"
                    logger.error(f"Задание для URL {url} не выполнено: {error}")
                    return "failed", None

                elif job_status == "running":
                    # Задание все еще выполняется
                    logger.info(
                        f"Задание {job_id} все еще выполняется. Ожидание {wait_time} секунд..."
                    )
                    time.sleep(wait_time)
                    continue

                else:
                    logger.warning(f"Неизвестный статус задания {job_id}: {job_status}")
                    time.sleep(wait_time)
                    continue

            except Exception as e:
                logger.error(f"Ошибка при проверке статуса задания {job_id}: {str(e)}")
                time.sleep(wait_time)

        # Если мы дошли до этой точки, значит все попытки исчерпаны
        logger.error(f"Превышено количество попыток проверки статуса задания {job_id}")
        return "timeout", None

    def get_hash_filename_from_url(self, url):
        """
        Создает имя файла на основе хеша URL

        Args:
            url: URL страницы

        Returns:
            Имя файла для сохранения HTML в формате hash.html
        """
        try:
            import hashlib

            # Используем полный md5 хеш URL
            url_hash = hashlib.md5(url.encode()).hexdigest()

            # Формируем имя файла в формате hash.html
            filename = f"{url_hash}.html"

            return filename
        except Exception as e:
            logger.error(f"Ошибка при создании хеш-имени файла из URL {url}: {str(e)}")
            # Возвращаем запасной вариант имени файла
            return self.get_filename_from_url(url)

    def submit_jobs(self, sheet_urls):
        """
        Отправляет задания на скрапинг для всех URL (только асинхронный API)

        Args:
            sheet_urls: Dictionary mapping sheet names to lists of URLs

        Returns:
            True if any jobs were submitted, False otherwise
        """
        total_submitted = 0
        total_processed = 0

        for sheet_name, urls in sheet_urls.items():
            logger.info(f"Обработка листа '{sheet_name}' ({len(urls)} URL)")

            sheet_name = sheet_name.strip()  # Удаляет пробелы в начале и конце
            sheet_dir = self.base_html_dir / sheet_name

            for url in urls:
                total_processed += 1
                # Формируем имя файла на основе URL
                # clean_url = url.strip()

                # Получаем имя файла на основе домена и пути (более читаемое имя)
                filename = self.get_hash_filename_from_url(url)
                html_file = sheet_dir / filename

                # Если файл уже существует, пропускаем
                if html_file.exists():
                    logger.info(f"Файл {html_file} уже существует, пропускаем")
                    continue

                # Проверяем, нет ли уже задания для этого URL
                existing_job = self._find_existing_job(url)
                if existing_job:
                    logger.info(f"Для URL {url} уже есть задание, проверяем его статус")

                    # Проверяем статус задания
                    job_status, html_content = self.check_existing_job_status(
                        existing_job
                    )

                    if job_status == "finished" and html_content:
                        # Сохраняем HTML
                        with open(html_file, "w", encoding="utf-8") as f:
                            f.write(html_content)

                        logger.info(
                            f"URL {url} успешно получен из существующего задания и сохранен в {html_file}"
                        )
                        total_submitted += 1

                        # Удаляем JSON файл задания
                        try:
                            json_file = self.json_dir / f"{existing_job['id']}.json"
                            json_file.unlink()  # Удаляем файл
                            logger.info(f"Файл задания {json_file} удален")
                        except Exception as e:
                            logger.error(f"Ошибка при удалении файла задания: {str(e)}")

                        continue

                    else:
                        # Задание все еще выполняется, пропускаем URL
                        continue

                # Отправляем новое задание через асинхронный API
                success = False
                max_retries = 3

                for attempt in range(max_retries):
                    try:
                        # Используем асинхронный API
                        response = requests.post(
                            url="https://async.scraperapi.com/jobs",
                            json={
                                "apiKey": self.api_key,
                                "url": url,
                            },
                            timeout=30,
                        )

                        if response.status_code == 200:
                            response_data = response.json()
                            job_id = response_data.get("id")

                            # Сохраняем информацию о задании
                            job_info = {
                                "id": job_id,
                                "url": url,
                                "sheet_name": sheet_name,
                                "html_file": str(html_file),
                                "status": "submitted",
                                "submitted_at": time.time(),
                            }

                            json_file = self.json_dir / f"{job_id}.json"
                            with open(json_file, "w", encoding="utf-8") as f:
                                json.dump(job_info, f, indent=4)

                            logger.info(
                                f"Асинхронное задание {job_id} отправлено для URL {url}"
                            )
                            total_submitted += 1
                            success = True
                            break
                        else:
                            logger.error(
                                f"Ошибка при отправке задания для URL {url}: {response.status_code} - {response.text}"
                            )
                            time.sleep((attempt + 1) * 2)

                    except Exception as e:
                        logger.error(
                            f"Ошибка при отправке задания для URL {url}: {str(e)}"
                        )
                        time.sleep((attempt + 1) * 2)

                if not success:
                    logger.error(
                        f"Не удалось отправить задание для URL {url} после {max_retries} попыток"
                    )

        logger.info(
            f"Всего обработано {total_processed} URL, отправлено заданий: {total_submitted}"
        )
        return total_submitted > 0

    def _find_existing_job(self, url):
        """Проверяет, есть ли уже задание для указанного URL"""
        for json_file in self.json_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    job_info = json.load(f)

                if job_info.get("url") == url:
                    return job_info
            except Exception as e:
                logger.error(f"Ошибка при чтении файла задания {json_file}: {str(e)}")
                pass

        return None

    async def fetch_results_async(self):
        """
        Асинхронно получает результаты заданий
        """
        logger.info("Проверка статуса существующих заданий...")

        active_jobs = 0
        completed_jobs = 0
        failed_jobs = 0

        for json_file in self.json_dir.glob("*.json"):
            try:

                with open(json_file, "r", encoding="utf-8") as f:
                    job_info = json.load(f)

                job_id = job_info.get("id")
                url = job_info.get("url")
                html_file_path = job_info.get("html_file")
                html_file = Path(html_file_path)
                html_file.parent.mkdir(parents=True, exist_ok=True)

                # Если файл уже существует, удаляем задание и пропускаем
                if html_file.exists():
                    try:
                        json_file.unlink()  # Удаляем файл задания
                        logger.info(f"HTML уже существует, задание {job_id} удалено")
                        completed_jobs += 1
                    except Exception as e:
                        logger.error(f"Ошибка при удалении файла задания: {str(e)}")
                    continue

                active_jobs += 1

                # Проверяем статус задания
                job_status, html_content = self.check_existing_job_status(job_info)

                if job_status == "finished" and html_content:
                    # Сохраняем HTML
                    try:
                        html_file.parent.mkdir(parents=True, exist_ok=True)

                        with open(html_file, "w", encoding="utf-8") as f:
                            f.write(html_content)

                        logger.info(
                            f"URL {url} успешно получен и сохранен в {html_file}"
                        )

                        # Удаляем файл задания
                        json_file.unlink()
                        logger.info(f"Файл задания {job_id} удален")

                        completed_jobs += 1
                        active_jobs -= 1
                    except Exception as e:
                        logger.error(
                            f"Ошибка при сохранении HTML или удалении файла задания: {str(e)}"
                        )

                elif job_status == "failed" or job_status == "timeout":
                    # Удаляем файл неудачного задания
                    try:
                        json_file.unlink()
                        logger.info(f"Файл неудачного задания {job_id} удален")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении файла задания: {str(e)}")

                    failed_jobs += 1
                    active_jobs -= 1

                # Если задание еще выполняется, просто продолжаем

            except Exception as e:
                logger.error(f"Ошибка при обработке файла {json_file}: {str(e)}")

        logger.info(
            f"Статус заданий: активных - {active_jobs}, завершенных - {completed_jobs}, неудачных - {failed_jobs}"
        )

        # Проверяем, остались ли активные задания
        if active_jobs > 0:
            logger.info(
                f"Еще есть {active_jobs} активных заданий. Подождем и проверим снова..."
            )
            # Увеличиваем задержку до 30 секунд
            await asyncio.sleep(30)
            return await self.fetch_results_async()

        return True

    async def main(self):
        """Основная функция для запуска процесса скрапинга"""
        # Проверяем наличие заданий
        if list(self.json_dir.glob("*.json")):
            logger.info("Найдены существующие задания, получаем результаты")
            await self.fetch_results_async()

        # Извлекаем URL из Excel
        sheet_urls = self.extract_urls_from_excel()

        # Отправляем задания через асинхронный API
        if self.submit_jobs(sheet_urls):
            logger.info("Задания отправлены, получаем результаты")
            await self.fetch_results_async()
        else:
            logger.warning("Нет URL для обработки или все файлы уже существуют")

        return True


# Пример использования
if __name__ == "__main__":

    scraper = ExcelSheetScraper(API_KEY, excel_file)

    # Запуск асинхронной функции в синхронном контексте
    import asyncio

    asyncio.run(scraper.main())
