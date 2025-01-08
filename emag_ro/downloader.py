import asyncio
import json
import time

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

    def dowload_json(self, json_file):
        with open(json_file, "r", encoding="utf-8") as file:
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

    def get_all_page_html(self):
        # Загрузка первой страницы и определение max_page
        payload = {
            "api_key": self.api_key,
            "url": self.url_start,
        }

        if self.use_ultra_premium:
            payload["ultra_premium"] = "true"
        else:
            payload["premium"] = True

        response = self.make_request_with_retries(
            "https://api.scraperapi.com/", payload, MAX_RETRIES, RETRY_DELAY
        )
        if not response:
            raise Exception(
                "Не удалось загрузить первую страницу после нескольких попыток."
            )

        src = response.text
        # logger.info(src)
        max_page = self.parser.parsing_page_max_page(src)

        self.tg_bot.send_message(f"Всего страниц {max_page}")
        logger.info(f"Всего страниц {max_page}")

        # Обработка первой страницы
        all_data = set()
        url_r = self.parser.parsin_page_json(src, 1)
        if url_r:
            all_data.update(url_r)
            logger.info(f"Первая страница обработана, найдено {len(url_r)} ссылок.")
        else:
            logger.warning("Не удалось обработать первую страницу.")

        # Обработка остальных страниц
        consecutive_none_count = 0  # Счётчик для подряд идущих None

        for page in range(2, max_page + 1):
            page_payload = {
                "api_key": self.api_key,
                "url": f"{self.url_start}&p={page}",
                "ultra_premium": "true",
            }
            response = self.make_request_with_retries(
                "https://api.scraperapi.com/", page_payload, MAX_RETRIES, RETRY_DELAY
            )
            if not response:
                logger.error(f"Пропущена страница {page} после {MAX_RETRIES} попыток.")
                continue

            src = response.text
            url_r = self.parser.parsin_page_json(src, page)

            if url_r:
                consecutive_none_count = (
                    0  # Сбрасываем счётчик, так как данные получены
                )
                before_update = len(all_data)
                all_data.update(url_r)
                added_count = len(all_data) - before_update
                logger.info(
                    f"Страница {page} обработана. Уникальных ссылок добавлено: {added_count}"
                )
            else:
                consecutive_none_count += 1
                logger.warning(f"На странице {page} нет товаров по вашему критерию")
                # logger.warning(
                #     f"Не удалось обработать страницу {page}. Подряд None: {consecutive_none_count}"
                # )

                # Если два раза подряд получено None, выходим из цикла
                if consecutive_none_count >= 2:
                    logger.info(
                        "Достигнут лимит подряд страниц по вашему критерию Завершаем обработку."
                    )
                    # logger.info(
                    #     "Достигнут лимит подряд страниц с результатом None. Завершаем обработку."
                    # )
                    break

        logger.info(f"Всего ссылок {len(all_data)}")
        self.tg_bot.send_message(f"Всего ссылок {len(all_data)}")

        self.writer.save_to_csv(all_data)

    # Рабочий код
    # def get_all_page_html(self):
    #     """Получает HTML всех страниц пагинации и сохраняет уникальные ссылки.

    #     Функция использует ScraperAPI для получения HTML всех страниц пагинации.
    #     Сначала загружается первая страница, определяется общее количество страниц (`max_page`),
    #     затем поочередно обрабатываются остальные страницы для получения уникальных ссылок.

    #     Основные шаги работы функции:
    #     1. **Получение первой страницы и определение `max_page`**:
    #         - Используется ScraperAPI для получения HTML кода.
    #         - Если запрос успешен (статус 200), парсится количество страниц (`max_page`) и собираются ссылки.
    #         - При ошибке (например, проблемы с сетью или доступом) происходит повтор запроса до достижения `MAX_RETRIES`.

    #     2. **Обработка остальных страниц**:
    #         - Для каждой страницы (начиная с 2) собираются ссылки и добавляются в множество `all_data`.
    #         - При отсутствии новых ссылок на текущей странице (`added_count == 0`), увеличивается счетчик `consecutive_no_additions`.
    #         - Если подряд были обработаны `max_no_additions` страниц без добавления новых ссылок, обработка завершается, чтобы не перегружать API.

    #     Примечания:
    #     - Лимит на количество повторов попыток (`MAX_RETRIES`) и задержка между попытками (`RETRY_DELAY`) используются для обработки ошибок.
    #     - Функция использует метод `parsing_page_max_page()` для извлечения количества страниц и `parsin_page()` для извлечения ссылок с каждой страницы.
    #     - В конце работы функция сохраняет все уникальные ссылки в CSV файл с помощью метода `save_to_csv()`.

    #     Args:
    #         self: Экземпляр класса, содержащий параметры, такие как `api_key`, `url_start`, и пути к файлам для сохранения результатов.

    #     Исключения:
    #     - Если первая страница не может быть загружена после нескольких попыток, вызывается исключение для прерывания выполнения.
    #     - Для каждой страницы при превышении количества попыток добавляется сообщение в лог и страница пропускается.

    #     Логгирование:
    #     - Функция активно логирует каждый этап обработки, включая успешную загрузку, ошибки при запросах,
    #     количество добавленных ссылок, а также случаи, когда страница была пропущена.

    #     Использование:
    #     - Эта функция полезна для сбора всех ссылок с пагинации, например, для парсинга сайтов электронной коммерции или каталогов.
    #     """
    #     payload = {
    #         "api_key": self.api_key,
    #         "url": self.url_start,
    #         "ultra_premium": "true",
    #     }
    #     # logger.info(payload)
    #     all_data = set()
    #     retries = 0
    #     # Добавляем обработку None с повторной попыткой
    #     url_r = None
    #     retry_json_attempts = 0  # Счётчик попыток обработки JSON
    #     max_json_retries = 10  # Максимальное количество попыток

    #     # Загрузка первой страницы и определение max_page
    #     while True:
    #         try:
    #             r = requests.get(
    #                 "https://api.scraperapi.com/", params=payload, timeout=60
    #             )
    #             if r.status_code == 200:
    #                 src = r.text
    #                 page_number = 1
    #                 max_page = self.parser.parsing_page_max_page(src)
    #                 logger.info(f"Всего страниц {max_page}")
    #                 while url_r is None and retry_json_attempts < max_json_retries:
    #                     url_r = self.parser.parsin_page_json(src, page_number)
    #                     if url_r is None:
    #                         retry_json_attempts += 1
    #                         logger.warning(
    #                             f"Не удалось обработать страницу. Повторная попытка {retry_json_attempts}/{max_json_retries}."
    #                         )
    #                         time.sleep(RETRY_DELAY)

    #                     if url_r is None:
    #                         logger.error(
    #                             "Не удалось обработать страницу после нескольких попыток."
    #                         )
    #                         retries += 1
    #                         if retries >= MAX_RETRIES:
    #                             logger.error(
    #                                 f"Пропущена страница {page_number} после {MAX_RETRIES} попыток."
    #                             )
    #                             break
    #                         continue  # Переходим к следующей итерации основного цикла

    #                 all_data.update(url_r)
    #                 logger.info(
    #                     f"Первая страница обработана, найдено {len(url_r)} ссылок."
    #                 )
    #                 break
    #             else:
    #                 logger.error(f"Ошибка при запросе первой страницы: {r.status_code}")
    #                 retries += 1
    #                 if retries >= MAX_RETRIES:
    #                     raise Exception("Превышено максимальное количество попыток.")
    #                 time.sleep(RETRY_DELAY)
    #         except Exception as e:
    #             logger.error(f"Ошибка при запросе первой страницы: {e}")
    #             retries += 1
    #             if retries >= MAX_RETRIES:
    #                 raise Exception(
    #                     "Не удалось загрузить первую страницу после попыток."
    #                 )
    #             time.sleep(RETRY_DELAY)

    #     # Обработка остальных страниц
    #     consecutive_no_additions = 0
    #     max_no_additions = 2

    #     for page in range(2, max_page + 1):
    #         page_payload = {
    #             "api_key": self.api_key,
    #             "url": f"{self.url_start}&p={page}",
    #             "ultra_premium": "true",
    #         }
    #         retries = 0

    #     while True:
    #         try:
    #             r = requests.get(
    #                 "https://api.scraperapi.com/", params=page_payload, timeout=60
    #             )
    #             if r.status_code == 200:
    #                 src = r.text
    #                 # Добавляем обработку None с повторной попыткой
    #                 url_r = None
    #                 retry_json_attempts = 0  # Счётчик попыток обработки JSON
    #                 max_json_retries = 10  # Максимальное количество попыток
    #                 while url_r is None and retry_json_attempts < max_json_retries:
    #                     url_r = self.parser.parsin_page_json(src, page)
    #                     if url_r is None:
    #                         retry_json_attempts += 1
    #                         logger.warning(
    #                             f"Не удалось обработать страницу. Повторная попытка {retry_json_attempts}/{max_json_retries}."
    #                         )
    #                         time.sleep(RETRY_DELAY)

    #                 if url_r is None:
    #                     logger.error(
    #                         "Не удалось обработать страницу после нескольких попыток."
    #                     )
    #                     retries += 1
    #                     if retries >= MAX_RETRIES:
    #                         logger.error(
    #                             f"Пропущена страница {page} после {MAX_RETRIES} попыток."
    #                         )
    #                         break
    #                     continue  # Переходим к следующей итерации основного цикла
    #                 before_update = len(all_data)
    #                 all_data.update(url_r)
    #                 added_count = len(all_data) - before_update
    #                 logger.info(
    #                     f"Страница {page} обработана. Уникальных ссылок добавлено: {added_count}"
    #                 )

    #                 if added_count == 0:
    #                     consecutive_no_additions += 1
    #                     logger.info(
    #                         f"На странице {page} не добавлено новых ссылок. Подряд страниц без добавлений: {consecutive_no_additions}"
    #                     )
    #                     if consecutive_no_additions >= max_no_additions:
    #                         logger.info(
    #                             "Достигнут лимит подряд страниц без добавлений. Завершаем обработку."
    #                         )
    #                         logger.info(f"Всего ссылок {len(all_data)}")
    #                         self.writer.save_to_csv(
    #                             all_data
    #                         )  # Сохраняем данные в CSV после завершения
    #                         return all_data
    #                 else:
    #                     consecutive_no_additions = 0
    #                 break  # Успешно обработали страницу, выходим из цикла
    #             else:
    #                 logger.error(
    #                     f"Ошибка при запросе страницы {page}: {r.status_code}"
    #                 )
    #                 retries += 1
    #                 if retries >= MAX_RETRIES:
    #                     logger.error(
    #                         f"Пропущена страница {page} после {MAX_RETRIES} попыток."
    #                     )
    #                     break
    #                 time.sleep(RETRY_DELAY)
    #         except Exception as e:
    #             logger.error(f"Ошибка при запросе страницы {page}: {e}")
    #             retries += 1
    #             if retries >= MAX_RETRIES:
    #                 logger.error(
    #                     f"Пропущена страница {page} после {MAX_RETRIES} попыток."
    #                 )
    #                 break
    #             time.sleep(RETRY_DELAY)
    # logger.info(f"Всего ссылок {len(all_data)}")
    # self.writer.save_to_csv(all_data)  # Сохраняем данные в CSV после завершения

    #     # return all_data

    def remove_query_parameters(self, url):
        # Разбираем URL
        parsed_url = urlparse(url)
        # Убираем параметры запроса (query)
        clean_url = urlunparse(parsed_url._replace(query=""))
        return clean_url

    # async def fetch_results_async(self):
    #     while True:
    #         all_finished = True
    #         for json_file in self.json_scrapy.glob("*.json"):
    #             try:
    #                 with open(json_file, "r", encoding="utf-8") as file:
    #                     response_data = json.load(file)
    #                 name_file = response_data.get("id")
    #                 html_company = self.html_files_directory / f"{name_file}.json"
    #                 # Если файл HTML уже существует, удаляем JSON файл и пропускаем
    #                 if html_company.exists():
    #                     logger.info(
    #                         f"Файл {html_company} уже существует, удаляем JSON файл и пропускаем."
    #                     )
    #                     try:
    #                         json_file.unlink()
    #                     except PermissionError as e:
    #                         logger.error(f"Не удалось удалить файл {json_file}: {e}")
    #                     continue

    #                 status_url = response_data.get("statusUrl")
    #                 try:
    #                     response = requests.get(url=status_url, timeout=30)
    #                     if response.status_code == 200:
    #                         job_status = response.json().get("status")
    #                         if job_status == "finished":
    #                             extracted_body = (
    #                                 response.json().get("response").get("body")
    #                             )
    #                             if extracted_body:
    #                                 try:
    #                                     cleaned_body = json.loads(extracted_body)
    #                                     # Сохранение результата в новый JSON-файл
    #                                     with open(
    #                                         output_path, "w", encoding="utf-8"
    #                                     ) as output_file:
    #                                         json.dump(
    #                                             cleaned_body,
    #                                             output_file,
    #                                             indent=4,
    #                                             ensure_ascii=False,
    #                                         )
    #                                 except json.JSONDecodeError as e:
    #                                     logger.error(
    #                                         f"Ошибка при декодировании JSON из 'body': {e}"
    #                                     )
    #                                     logger.error("Содержимое 'body':")
    #                                     logger.error(extracted_body)
    #                             else:
    #                                 print("Поле 'body' пустое или отсутствует в файле.")
    #                             # logger.info(
    #                             #     f"Результаты для {status_url} сохранены в файл {html_company}"
    #                             # )
    #                             logger.info(
    #                                 f"Результаты сохранены в файл {html_company}"
    #                             )
    #                             # Удаление JSON файла после успешного сохранения результата
    #                             try:
    #                                 json_file.unlink()
    #                             except PermissionError as e:
    #                                 logger.error(
    #                                     f"Не удалось удалить файл {json_file}: {e}"
    #                                 )
    #                         else:
    #                             all_finished = False
    #                             logger.info(
    #                                 f"Статус задачи для {status_url}: {job_status}"
    #                             )
    #                     else:
    #                         all_finished = False  # Еще есть незавершенные задачи
    #                         logger.error(
    #                             f"Ошибка при получении статуса задачи: {response.status_code}"
    #                         )
    #                 except requests.exceptions.ReadTimeout:
    #                     logger.error("Тайм-аут при обработке, задача будет повторена")
    #                     all_finished = False

    #                 except requests.exceptions.SSLError as e:
    #                     logger.error(f"SSL ошибка: {e}, задача будет повторена")
    #                     all_finished = False

    #                 except requests.exceptions.RequestException as e:
    #                     logger.error(f"Ошибка запроса: {e}, задача будет повторена")
    #                     all_finished = False
    #             except PermissionError as e:
    #                 logger.error(f"Не удалось открыть файл {json_file}: {e}")
    #                 all_finished = False  # Еще есть незавершенные задачи
    #         if all_finished:
    #             break
    #         # Подождите 10 секунд перед повторной проверкой
    #         await asyncio.sleep(10)

    # # Функция для отправки задач на ScraperAPI

    # def submit_jobs(self):
    #     urls = self.read_cities_from_csv(self.csv_output_file)
    #     if not urls:  # Проверяем, если список пуст
    #         logger.error("Список URL пуст. Завершаю выполнение.")
    #         return False  # Возвращаем статус False для прекращения выполнения
    #     batch_size = 40000  # Размер каждой порции URL
    #     # Разделяем список urls на подсписки по batch_size
    #     for i in range(0, len(urls), batch_size):
    #         url_batch = urls[i : i + batch_size]  # Берем следующую порцию до 50 000
    #         for url in url_batch:
    #             cleaned_url = self.remove_query_parameters(url)
    #             name_file = url.split("/")[-1].replace("-", "_")
    #             html_company = self.html_files_directory / f"{name_file}.html"
    #             # Если файл HTML уже существует, удаляем JSON файл и пропускаем
    #             if html_company.exists():
    #                 continue
    #             success = False
    #             # Бесконечный цикл до успешного выполнения
    #             # logger.info(cleaned_url)
    #             while not success:
    #                 try:
    #                     res_json = {
    #                         "apiKey": self.api_key,
    #                         "apiParams": {},
    #                         "url": cleaned_url,
    #                     }

    #                     # Выбор параметра в зависимости от self.use_ultra_premium
    #                     if self.use_ultra_premium:
    #                         res_json["apiParams"]["ultra_premium"] = "true"
    #                     else:
    #                         res_json["apiParams"]["premium"] = True

    #                     response = requests.post(
    #                         url="https://async.scraperapi.com/jobs",
    #                         json=res_json,
    #                         timeout=30,
    #                     )
    #                     if response.status_code == 200:
    #                         response_data = response.json()
    #                         job_id = response_data.get("id")
    #                         json_file = self.json_scrapy / f"{job_id}.json"
    #                         with open(json_file, "w", encoding="utf-8") as file:
    #                             json.dump(response_data, file, indent=4)
    #                         # logger.info(f"Задача отправлена для URL {cleaned_url}")
    #                         success = True
    #                     else:
    #                         logger.error(
    #                             f"Ошибка при отправке задачи для URL {cleaned_url}: {response.status_code}"
    #                         )
    #                         self.tg_bot.send_message(
    #                             f"Ошибка при отправке задачи для URL {cleaned_url}: {response.status_code}"
    #                         )
    #                 except requests.exceptions.ReadTimeout:
    #                     logger.error("Тайм-аут при обработке")
    #                 except requests.exceptions.SSLError as e:
    #                     logger.error("SSL ошибка")
    #                 except requests.exceptions.RequestException as e:
    #                     logger.error(f"Ошибка запроса для ")
    #                 except Exception as e:
    #                     logger.error(f"Неизвестная ошибка ")
    #     return True  # Возвращаем True, если задачи успешно отправлены

    # def submit_job(self, url):
    #     # URL для работы с API
    #     api_url = "https://async.scraperapi.com/jobs"

    #     # Целевой URL с уже сформированными параметрами
    #     target_url = (
    #         "https://www.emag.ro/search-by-url"
    #         "?source_id=7"
    #         "&templates[]=full"
    #         "&sort[popularity_v_opt]=desc"
    #         "&listing_display_id=2"
    #         "&page[limit]=100"
    #         "&page[offset]=0"
    #         "&fields[items][image_gallery][fashion][limit]=2"
    #         "&fields[items][image][resized_images]=1"
    #         "&fields[items][resized_images]=200x200,350x350,720x720"
    #         "&fields[items][flags]=1"
    #         "&fields[items][offer][buying_options]=1"
    #         "&fields[items][offer][flags]=1"
    #         "&fields[items][offer][bundles]=1"
    #         "&fields[items][offer][gifts]=1"
    #         "&fields[items][characteristics]=listing"
    #         "&fields[quick_filters]=1"
    #         "&search_id="
    #         "&search_fraze="
    #         "&search_key="
    #         f"&url={url}"
    #     )

    #     # Пользовательские заголовки
    #     headers = {
    #         "accept": "application/json",
    #         "accept-language": "ru,en;q=0.9,uk;q=0.8",
    #         "content-type": "application/json",  # Устанавливаем Content-Type для JSON
    #         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    #     }

    #     # Тело запроса для ScraperAPI
    #     payload = {
    #         "apiKey": "7757eea384bafff7726179e7855bb664",  # Ваш API-ключ
    #         "url": target_url,  # Целевой URL
    #         "keep_headers": True,  # Указываем, что используем свои заголовки
    #         "method": "GET",  # HTTP-метод
    #     }
    #     # Отправка POST-запроса к ScraperAPI
    #     try:
    #         response = requests.post(api_url, json=payload, headers=headers)
    #         if response.status_code == 200:
    #             response_data = response.json()
    #             job_id = response_data.get("id")
    #             json_file = self.json_scrapy / f"{job_id}.json"
    #             with open(json_file, "w", encoding="utf-8") as file:
    #                 json.dump(response_data, file, indent=4)
    #         else:
    #             logger.error(
    #                 f"Ошибка при отправке задачи для URL {url}: {response.status_code}"
    #             )
    #             self.tg_bot.send_message(
    #                 f"Ошибка при отправке задачи для URL {url}: {response.status_code}"
    #             )
    #     except requests.exceptions.ReadTimeout:
    #         logger.error("Тайм-аут при обработке")
    #     except requests.exceptions.SSLError as e:
    #         logger.error("SSL ошибка")
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"Ошибка запроса для ")
    #     except Exception as e:
    #         logger.error(f"Неизвестная ошибка ")

    # # Функция для чтения городов из CSV файла

    # def read_cities_from_csv(self, input_csv_file):
    #     df = pd.read_csv(input_csv_file)
    #     return df["url"].tolist()

    # # Основная функция для скачивания всех товаров
    # async def main_url(self):
    #     if any(self.json_scrapy.glob("*.json")):
    #         await self.fetch_results_async()
    #     else:
    #         # Проверяем результат отправки задач
    #         if not self.submit_jobs():
    #             return False  # Прерываем выполнение, если список URL пуст
    #         await self.fetch_results_async()
    #     return True  # Успешное выполнение
