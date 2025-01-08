import asyncio
import json
import time
from pathlib import Path

# from parser import Parser
from urllib.parse import urlparse, urlunparse

import pandas as pd
import requests
from configuration.logger_setup import logger

# from writer import Writer

# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 10
RETRY_DELAY = 30  # Задержка между попытками в секундах


class Downloader:

    def __init__(
        self,
        min_count,
        api_key,
        html_files_directory,
        csv_output_file,
        json_products,
        json_scrapy,
        url_start,
        max_workers,
        json_result,
        xlsx_result,
        json_page_directory,
        use_ultra_premium,
        # tg_bot,
        json_files_directory,
    ):

        self.min_count = min_count
        self.api_key = api_key
        self.html_files_directory = html_files_directory
        self.json_files_directory = json_files_directory
        self.csv_output_file = csv_output_file
        self.json_products = json_products
        self.json_scrapy = json_scrapy
        self.url_start = url_start
        self.max_workers = max_workers
        self.json_result = json_result
        self.xlsx_result = xlsx_result
        self.json_page_directory = json_page_directory
        self.use_ultra_premium = use_ultra_premium
        # self.tg_bot = tg_bot

        # self.parser = Parser(
        #     min_count,
        #     html_files_directory,
        #     csv_output_file,
        #     max_workers,
        #     json_products,
        #     json_page_directory,
        #     use_ultra_premium,
        #     tg_bot,
        #     json_files_directory,
        # )  # Создаем экземпляр Parser
        # self.writer = Writer(
        #     csv_output_file,
        #     json_result,
        #     xlsx_result,
        #     use_ultra_premium,
        #     tg_bot,
        #     json_files_directory,
        # )

    def make_request_with_retries(self, url, params, max_retries=10, delay=30):
        """
        Делает запрос с повторными попытками.

        Args:
            url (str): URL для запроса.
            params (dict): Параметры запроса.
            max_retries (int): Максимальное количество попыток.
            delay (int): Задержка между попытками в секундах.

        Returns:
            Response | None: Успешный ответ или None, если все попытки исчерпаны.
        """
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(url, params=params, timeout=60)
                if response.status_code == 200:
                    logger.info(f"Запрос успешен: {url}")
                    return response
                else:
                    logger.warning(
                        f"Ошибка {response.status_code} при запросе {url}. Попытка {retries + 1}/{max_retries}."
                    )
            except Exception as e:
                logger.error(
                    f"Ошибка при выполнении запроса: {e}. Попытка {retries + 1}/{max_retries}."
                )
            retries += 1
            time.sleep(delay)

        logger.error(f"Не удалось выполнить запрос после {max_retries} попыток: {url}")
        self.tg_bot.send_message(
            f"Не удалось выполнить запрос после {max_retries} попыток: {url}"
        )
        return None

    def get_last_page_id(self, response_data):
        """
        Извлекает последнее значение 'id' из списка 'pages' в объекте 'pagination'.

        :param response_data: словарь с данными ответа, содержащего пагинацию.
        :return: последнее значение 'id' или None, если данные отсутствуют.
        """
        try:
            # Безопасно переходим через уровни data -> pagination -> pages
            pagination = response_data.get("data", {}).get("pagination", {})
            pages = pagination.get("pages", [])

            if pages:
                # Берем последний элемент из списка страниц и его id
                return pages[-1].get("id")
            return None
        except AttributeError:
            logger.error("Переданные данные не являются словарём.")
            return None

    def get_all_page_json(self, base, suffix):
        url = f"/{base}/{suffix}"
        # URL для работы с API
        api_url = "https://async.scraperapi.com/jobs"

        # Целевой URL с уже сформированными параметрами
        target_url = (
            "https://www.emag.ro/search-by-url"
            "?source_id=7"
            "&templates[]=full"
            "&sort[popularity_v_opt]=desc"
            "&listing_display_id=2"
            "&page[limit]=100"
            "&page[offset]=0"
            "&fields[items][image_gallery][fashion][limit]=2"
            "&fields[items][image][resized_images]=1"
            "&fields[items][resized_images]=200x200,350x350,720x720"
            "&fields[items][flags]=1"
            "&fields[items][offer][buying_options]=1"
            "&fields[items][offer][flags]=1"
            "&fields[items][offer][bundles]=1"
            "&fields[items][offer][gifts]=1"
            "&fields[items][characteristics]=listing"
            "&fields[quick_filters]=1"
            "&search_id="
            "&search_fraze="
            "&search_key="
            f"&url={url}"
        )

        # Пользовательские заголовки
        headers = {
            "accept": "application/json",
            "accept-language": "ru,en;q=0.9,uk;q=0.8",
            "content-type": "application/json",  # Устанавливаем Content-Type для JSON
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        # Тело запроса для ScraperAPI
        payload = {
            "apiKey": "b7141d2b54426945a9f0bf6ab4c7bc54",  # Ваш API-ключ
            "url": target_url,  # Целевой URL
            "keep_headers": True,  # Указываем, что используем свои заголовки
            "method": "GET",  # HTTP-метод
        }
        # Отправка POST-запроса к ScraperAPI
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            logger.info("Успешный запрос!")
            response_data = response.json()
            job_id = response_data.get("id")
            json_file = self.json_scrapy / f"{job_id}.json"
            with open(json_file, "w", encoding="utf-8") as file:
                json.dump(response_data, file, indent=4)
            json_data = self.dowload_json(json_file)
            all_page = int(self.get_last_page_id(json_data))
            self.get_page_json(base, suffix, all_page)

        else:
            logger.error(f"Ошибка HTTP: {response.status_code}")
            logger.error(response.text)

    def dowload_json(self, json_scrapy):
        with open(json_scrapy, "r", encoding="utf-8") as file:
            response_data = json.load(file)

        status_url = response_data.get("statusUrl")
        max_retries = 100  # Максимальное количество проверок статуса
        retry_delay = 10  # Задержка между проверками (в секундах)
        for _ in range(max_retries):
            response = requests.get(url=status_url, timeout=30)
            if response.status_code == 200:
                json_response = response.json()
                job_status = json_response.get("status")
                logger.info(job_status)
                if job_status == "finished":
                    name_file = json_response.get("id")
                    # Сохраняем фалйы страниц
                    json_file = self.json_files_directory / f"{name_file}.json"
                    extracted_body = json_response.get("response", {}).get("body")

                    if extracted_body:
                        try:
                            # Попытка обработать содержимое "body" как JSON
                            cleaned_body = json.loads(extracted_body)

                            # Сохранение результата в файл
                            with open(json_file, "w", encoding="utf-8") as output_file:
                                json.dump(
                                    cleaned_body,
                                    output_file,
                                    indent=4,
                                    ensure_ascii=False,
                                )

                            logger.info(f"Результат сохранён в файл: {json_file}")
                            json_scrapy.unlink()
                            logger.info(f"Файл удален: {json_scrapy}")
                            return cleaned_body
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Ошибка при декодировании JSON из 'body': {e}"
                            )
                            logger.error(f"Содержимое 'body': {extracted_body}")
                            return
                else:
                    logger.info("Задача ещё не завершена, повторная проверка...")
                    time.sleep(retry_delay)  # Задержка перед следующим запросом

    def get_page_json(self, base, suffix, all_page):
        # URL для работы с API
        api_url = "https://async.scraperapi.com/jobs"
        for i in range(2, all_page + 1):
            url = f"/{base}/p{i}/{suffix}"
            # Целевой URL с уже сформированными параметрами
            target_url = (
                "https://www.emag.ro/search-by-url"
                "?source_id=7"
                "&templates[]=full"
                "&sort[popularity_v_opt]=desc"
                "&listing_display_id=2"
                "&page[limit]=100"
                "&page[offset]=0"
                "&fields[items][image_gallery][fashion][limit]=2"
                "&fields[items][image][resized_images]=1"
                "&fields[items][resized_images]=200x200,350x350,720x720"
                "&fields[items][flags]=1"
                "&fields[items][offer][buying_options]=1"
                "&fields[items][offer][flags]=1"
                "&fields[items][offer][bundles]=1"
                "&fields[items][offer][gifts]=1"
                "&fields[items][characteristics]=listing"
                "&fields[quick_filters]=1"
                "&search_id="
                "&search_fraze="
                "&search_key="
                f"&url={url}"
            )

            # Пользовательские заголовки
            headers = {
                "accept": "application/json",
                "accept-language": "ru,en;q=0.9,uk;q=0.8",
                "content-type": "application/json",  # Устанавливаем Content-Type для JSON
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }

            # Тело запроса для ScraperAPI
            payload = {
                "apiKey": "b7141d2b54426945a9f0bf6ab4c7bc54",  # Ваш API-ключ
                "url": target_url,  # Целевой URL
                "keep_headers": True,  # Указываем, что используем свои заголовки
                "method": "GET",  # HTTP-метод
            }
            # Отправка POST-запроса к ScraperAPI
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                logger.info("Успешный запрос!")
                response_data = response.json()
                job_id = response_data.get("id")
                json_file = self.json_scrapy / f"{job_id}.json"
                with open(json_file, "w", encoding="utf-8") as file:
                    json.dump(response_data, file, indent=4)
                self.dowload_json(json_file)

            else:
                logger.error(f"Ошибка HTTP: {response.status_code}")
                logger.error(response.text)
