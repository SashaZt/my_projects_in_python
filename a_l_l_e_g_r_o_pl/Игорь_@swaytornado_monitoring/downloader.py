import asyncio
import json
import re

import requests
from configuration.logger_setup import logger

# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 30
RETRY_DELAY = 30  # Задержка между попытками в секундах


class Downloader:

    def __init__(self, api_key, html_files_directory, urls, json_scrapy):
        self.api_key = api_key
        self.html_files_directory = html_files_directory
        self.urls = urls
        self.json_scrapy = json_scrapy

    async def fetch_results_async(self):
        while True:
            all_finished = True  # Флаг, показывающий, завершены ли все задачи
            for json_file in self.json_scrapy.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as file:
                        response_data = json.load(file)
                    name_file = response_data.get("url").split("/")[-1]
                    html_company = self.html_files_directory / f"{name_file}.html"

                    # Если файл HTML уже существует, удаляем JSON файл и пропускаем
                    if html_company.exists():
                        logger.info(
                            f"Файл {html_company} уже существует, удаляем JSON файл и пропускаем."
                        )
                        try:
                            json_file.unlink()
                        except PermissionError as e:
                            logger.error(f"Не удалось удалить файл {json_file}: {e}")
                        continue

                    # Выполняем запрос для статуса задачи
                    status_url = response_data.get("statusUrl")
                    try:
                        response = requests.get(url=status_url, timeout=60)
                        if response.status_code == 200:
                            job_status = response.json().get("status")
                            if job_status == "finished":
                                body = response.json().get("response").get("body")
                                with open(html_company, "w", encoding="utf-8") as file:
                                    file.write(body)
                                logger.info(
                                    f"Результаты для {status_url} сохранены в файл {html_company}"
                                )
                                # Удаление JSON файла после успешного сохранения результата
                                try:
                                    json_file.unlink()
                                except PermissionError as e:
                                    logger.error(
                                        f"Не удалось удалить файл {json_file}: {e}"
                                    )
                            else:
                                logger.info(
                                    f"Статус задачи для {status_url}: {job_status}"
                                )
                                all_finished = False  # Еще есть незавершенные задачи
                        else:
                            logger.error(
                                f"Ошибка при получении статуса задачи: {response.status_code}"
                            )
                            all_finished = False

                    except requests.exceptions.ReadTimeout:
                        logger.error("Тайм-аут при обработке, задача будет повторена")
                        all_finished = False

                    except requests.exceptions.SSLError as e:
                        logger.error(f"SSL ошибка: {e}, задача будет повторена")
                        all_finished = False

                    except requests.exceptions.RequestException as e:
                        logger.error(f"Ошибка запроса: {e}, задача будет повторена")
                        all_finished = False

                except Exception as e:
                    logger.error(f"Неизвестная ошибка: {e}, задача будет повторена")
                    all_finished = False

            if all_finished:
                logger.info("Все задачи успешно завершены!")
                break  # Все задачи завершены, выходим из цикла

            # Пауза перед повторной проверкой
            await asyncio.sleep(1)

    def extract_id(self, id_url):
        """
        Извлекает числовой идентификатор из URL или возвращает строку, если она уже состоит только из цифр.
        """
        # Если строка состоит только из цифр, возвращаем её
        if id_url.isdigit():
            return id_url

        # Шаблон для извлечения чисел из URL
        match = re.search(r"(\d+)$", id_url)
        if match:
            return match.group(1)  # Возвращаем найденное число

        # Если числа не найдено, возвращаем None или сообщение об ошибке
        return None

    # Функция для отправки задач на ScraperAPI
    def submit_jobs(self):
        batch_size = 40000  # Размер каждой порции URL
        # Разделяем список urls на подсписки по batch_size
        # self.urls - список url или id
        for i in range(0, len(self.urls), batch_size):
            id_batch = self.urls[i : i + batch_size]  # Берем следующую порцию до 50 000
            for id_url in id_batch:
                # Проверяем что пришло url или id
                url_id = self.extract_id(id_url)
                logger.info(url_id)
                html_company = self.html_files_directory / f"{url_id}.html"
                if html_company.exists():
                    continue
                url = f"https://allegro.pl/oferta/{url_id}"
                success = False
                # Бесконечный цикл до успешного выполнения
                while not success:
                    try:
                        response = requests.post(
                            url="https://async.scraperapi.com/jobs",
                            json={"apiKey": self.api_key, "url": url},
                            timeout=60,
                        )
                        if response.status_code == 200:
                            response_data = response.json()
                            job_id = response_data.get("id")
                            json_file = self.json_scrapy / f"{job_id}.json"
                            with open(json_file, "w", encoding="utf-8") as file:
                                json.dump(response_data, file, indent=4)
                            logger.info(f"Задача отправлена для URL {url}")
                            success = True  # Успешное выполнение, выходим из цикла
                        else:
                            logger.error(
                                f"Ошибка при отправке задачи для URL {url}: {response.status_code}"
                            )
                    except requests.exceptions.ReadTimeout:
                        logger.error("Тайм-аут при обработке")
                    except requests.exceptions.SSLError as e:
                        logger.error("SSL ошибка")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Ошибка запроса для ")
                    except Exception as e:
                        logger.error(f"Неизвестная ошибка ")

    # Функция для чтения городов из CSV файла

    def read_values_from_json(self, file_incoming):
        """
        Читает JSON-файл и возвращает список значений по указанному ключу.

        :param input_json_file: Путь к JSON-файлу
        :param key: Ключ, значения которого нужно извлечь
        :return: Список значений
        """
        with open(file_incoming, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            else:
                raise ValueError("Неверный формат JSON: ожидался список или словарь")

    # Основная функция для скачивания все товаров
    async def main_url(self):
        # Проверка наличия файлов в json_files_directory
        if any(self.json_scrapy.glob("*.json")):
            # Получение результатов задач, если есть несохраненные результаты
            await self.fetch_results_async()
        else:
            # Отправка задач на ScraperAPI, если json файлов нет
            self.submit_jobs()
            # Получение результатов задач
            await self.fetch_results_async()
