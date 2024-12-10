import ast
import asyncio
import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import demjson3
import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
# Настройте максимальное количество попыток, если требуется
MAX_RETRIES = 30
RETRY_DELAY = 30  # Задержка между попытками в секундах

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

start_sitemap = xml_directory / "sitemap.xml"
all_urls_page = data_directory / "all_urls.csv"
all_url_sitemap = data_directory / "sitemap.csv"


# # Функция загрузки списка прокси
# def load_proxies():
#     if os.path.exists(file_proxy):
#         with open(file_proxy, "r", encoding="utf-8") as file:
#             proxies = [line.strip() for line in file]
#         logger.info(f"Загружено {len(proxies)} прокси.")
#         return proxies
#     else:
#         logger.warning(
#             "Файл с прокси не найден. Работа будет выполнена локально без прокси."
#         )
#         return []


# # Функция для парсинга прокси
# def parse_proxy(proxy):
#     if "@" in proxy:
#         protocol, rest = proxy.split("://", 1)
#         credentials, server = rest.split("@", 1)
#         username, password = credentials.split(":", 1)
#         return {
#             "server": f"{protocol}://{server}",
#             "username": username,
#             "password": password,
#         }
#     else:
#         return {"server": f"http://{proxy}"}


# async def setup_proxy(proxy_data, tab):
#     async def auth_challenge_handler(event: fetch.AuthRequired):
#         # Ответ на запрос аутентификации
#         await tab.send(
#             fetch.continue_with_auth(
#                 request_id=event.request_id,
#                 auth_challenge_response=fetch.AuthChallengeResponse(
#                     response="ProvideCredentials",
#                     username=proxy_data.get("username"),
#                     password=proxy_data.get("password"),
#                 ),
#             )
#         )

#     async def req_paused(event: fetch.RequestPaused):
#         # Продолжение запроса
#         await tab.send(fetch.continue_request(request_id=event.request_id))

#     # Добавление обработчиков для событий fetch
#     tab.add_handler(
#         fetch.RequestPaused, lambda event: asyncio.create_task(req_paused(event))
#     )
#     tab.add_handler(
#         fetch.AuthRequired,
#         lambda event: asyncio.create_task(auth_challenge_handler(event)),
#     )

#     # Включение домена fetch с обработкой запросов аутентификации
#     await tab.send(fetch.enable(handle_auth_requests=True))


# # Получаем первый, стартовый sitemap
# async def get_sitemap():
#     # Открываем браузер
#     browser = (
#         await uc.start()
#     )  # Добавьте параметр headless=True, если не хотите видеть браузер
#     # Переходим на страницу
#     page = await browser.get("https://www.doctolib.de/sitemap.xml")
#     await asyncio.sleep(1)
#     content = await page.get_content()

#     # Проверяем, что содержимое не None
#     if content:
#         # Сохраняем в файл sitemap.xml
#         with open(sitemap_output_file, "w", encoding="utf-8") as f:
#             f.write(content)
#     else:
#         logger.error("Контент не найден.")

#     # Закрываем страницу
#     await page.close()


# Парсим первый стартовый sitemap
def parsing_start_sitemap():
    # Открываем файл sitemap.xml
    tree = ET.parse(start_sitemap)
    root = tree.getroot()

    # Собираем все URL из XML
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [elem.text.strip() for elem in root.findall(".//ns:loc", namespaces)]

    # Записываем в start_sitemap.csv
    df = pd.DataFrame({"url": urls})
    df.to_csv(start_sitemap, index=False)


def read_csv(file):
    # Читаем файл start_sitemap.csv и возвращаем список URL
    df = pd.read_csv(file)
    return df["url"].tolist()


def extract_urls_from_xml_files():

    # Создаем пустое множество для уникальных URL
    unique_urls = set()

    # Проходим по всем XML файлам в указанной директории
    for xml_file in Path(xml_files_directory).glob("*.xml"):
        with xml_file.open(encoding="utf-8") as file:
            content = file.read()
            # Парсим XML содержимое
            root = ET.fromstring(content)
            namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [elem.text.strip() for elem in root.findall(".//ns:loc", namespaces)]
            unique_urls.update(urls)

    # Записываем уникальные URL в all_urls.csv
    df = pd.DataFrame({"url": list(unique_urls)})
    df.to_csv(all_urls_page, index=False)


# async def get_all_urls():

#     urls = read_csv(all_urls_page)
#     browser = await uc.start(
#         browser_args=[f"--proxy-server={'185.112.13.176:2831'}"],
#     )  # Добавьте параметр headless=True, если не хотите видеть браузер

#     # Переходим на страницу
#     for url in urls[:1]:
#         file_name = f"{url.split('/')[-3].replace("-","_")}_{url.split('/')[-2].replace("-","_")}_{url.split('/')[-1].replace("-","_")}"
#         sitemap_output_file = xml_files_directory / file_name
#         url = "https://www.doctolib.de/radiologie-diagnostische/berlin/christian-enzweiler?pid=practice-9707"
#         main_tab = await browser.get(url)
#         await setup_fetch_intercept(main_tab)
#         await asyncio.sleep(20)
#         intercepted_url = await setup_fetch_intercept(main_tab)
#         if intercepted_url:
#             logger.info(f"Переход на перехваченный URL: {intercepted_url}")
#             await main_tab.goto(intercepted_url)
#         # content = await page.get_content()

#         # # Проверяем, что содержимое не None
#         # if content:
#         #     # Сохраняем в файл sitemap.xml
#     with open(sitemap_output_file, "w", encoding="utf-8") as f:
#         f.write(content)
# else:
#     logger.error("Контент не найден.")

# Закрываем страницу
# await page.close()


# async def setup_fetch_intercept(tab):
#     intercepted_url = None

#     async def req_paused(event: fetch.RequestPaused):
#         nonlocal intercepted_url
#         logger.info(f"Запрос приостановлен: {event.request.url}")
#         if (
#             "doctolib.de/online_booking/api/slot_selection_funnel/v1/"
#             in event.request.url
#         ):
#             intercepted_url = event.request.url
#             await tab.send(fetch.continue_request(request_id=event.request_id))
#         else:
#             await tab.send(fetch.continue_request(request_id=event.request_id))

#     tab.add_handler(
#         fetch.RequestPaused, lambda event: asyncio.create_task(req_paused(event))
#     )
#     await tab.send(
#         fetch.enable(
#             patterns=[
#                 fetch.RequestPattern(
#                     url_pattern="*doctolib.de/online_booking/api/slot_selection_funnel/v1/*",
#                     request_stage=fetch.RequestStage.RESPONSE,
#                 )
#             ],
#             handle_auth_requests=True,
#         )
#     )
#     await asyncio.sleep(2)  # Подождем, пока запрос будет перехвачен
#     return intercepted_url


# async def get_response_body(request_id, tab):
#     try:
#         response = await tab.send(fetch.get_response_body(request_id=request_id))
#         logger.info(f"Тело ответа получено для ID запроса: {request_id}")
#         return response.get("body") if response else None
#     except Exception as e:
#         logger.error(
#             f"Не удалось получить тело ответа для ID запроса: {request_id}, ошибка: {e}"
#         )
#         return None


# async def save_response_to_json(response_body):
#     try:
#         response_data = json.loads(response_body)
#         with open("intercepted_responses.json", "a", encoding="utf-8") as json_file:
#             json.dump(response_data, json_file, ensure_ascii=False, indent=4)
#             json_file.write(",\n")
#         logger.info("Тело ответа сохранено в intercepted_responses.json")
#     except json.JSONDecodeError:
#         logger.error("Не удалось декодировать JSON из тела ответа.")


def get_sitemap_start():

    url_start = "https://www.doctolib.de/sitemap.xml"
    payload = {
        "api_key": api_key,
        "url": url_start,
        # "ultra_premium": "true",
    }
    retries = 0
    while True:
        try:
            r = requests.get("https://api.scraperapi.com/", params=payload, timeout=60)
            if r.status_code == 200:
                with open(start_sitemap, "wb") as file:
                    file.write(r.content)
                logger.info(f"Скачан {start_sitemap}")
                break
            else:
                logger.error(f"Ошибка при запросе первой страницы: {r.status_code}")
                retries += 1
                if retries >= MAX_RETRIES:
                    raise Exception("Превышено максимальное количество попыток.")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Ошибка при запросе первой страницы: {e}")
            retries += 1
            if retries >= MAX_RETRIES:
                raise Exception("Не удалось загрузить первую страницу после попыток.")
            time.sleep(RETRY_DELAY)


def get_sitemap_all():
    all_url = read_csv(all_url_sitemap)
    for url in all_url:

        payload = {
            "api_key": api_key,
            "url": url,
            "keep_headers": "true",
            # "ultra_premium": "true",
        }
        retries = 0
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        file_name = f"{url.split('/')[-2]}_{url.split('/')[-1]}"
        sitemap_output_file = xml_files_directory / file_name
        if sitemap_output_file.exists():
            continue
        while True:
            try:

                r = requests.get(
                    "https://api.scraperapi.com/",
                    params=payload,
                    headers=headers,
                    timeout=60,
                )
                if r.status_code == 200:
                    with open(sitemap_output_file, "wb") as file:
                        file.write(r.content)
                    logger.info(f"Скачан {sitemap_output_file}")
                    break
                else:
                    logger.error(f"Ошибка при запросе первой страницы: {r.status_code}")
                    retries += 1
                    if retries >= MAX_RETRIES:
                        raise Exception("Превышено максимальное количество попыток.")
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"Ошибка при запросе первой страницы: {e}")
                retries += 1
                if retries >= MAX_RETRIES:
                    raise Exception(
                        "Не удалось загрузить первую страницу после попыток."
                    )
                time.sleep(RETRY_DELAY)


# Основная функция для скачивания все товаров
async def main_url():
    # Проверка наличия файлов в json_files_directory
    if any(json_directory.glob("*.json")):
        # Получение результатов задач, если есть несохраненные результаты
        await fetch_results_async()
    else:
        # Отправка задач на ScraperAPI, если json файлов нет
        submit_jobs()
        # Получение результатов задач
        await fetch_results_async()


async def fetch_results_async():
    while True:
        all_finished = True
        for json_file in json_directory.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as file:
                    response_data = json.load(file)
                url = response_data.get("url")
                # Формирование имени файла
                url_parts = url.split("/")
                last_part = url_parts[-1].split(
                    "?"
                )  # Разделяем последний сегмент по '?'

                # Основная часть имени
                base_name = "_".join(
                    part.replace("-", "_") for part in url_parts[-3:-1]
                )  # Берем последние три части (без query string)

                # Обработка query string (если есть)
                if len(last_part) > 1:
                    query_part = last_part[1].replace("=", "_").replace("-", "_")
                    file_name = f"{base_name}_{last_part[0].replace('-', '_')}_{query_part}.html"
                else:
                    file_name = f"{base_name}_{last_part[0].replace('-', '_')}.html"
                html_company = html_directory / file_name
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

                status_url = response_data.get("statusUrl")
                response = requests.get(url=status_url, timeout=30)
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
                            logger.error(f"Не удалось удалить файл {json_file}: {e}")
                    else:
                        all_finished = False
                        logger.info(f"Статус задачи для {status_url}: {job_status}")
                else:
                    logger.error(
                        f"Ошибка при получении статуса задачи: {response.status_code}"
                    )
            except PermissionError as e:
                logger.error(f"Не удалось открыть файл {json_file}: {e}")
        if all_finished:
            break
        # Подождите 10 секунд перед повторной проверкой
        await asyncio.sleep(10)


# Функция для отправки задач на ScraperAPI
def submit_jobs():
    urls = read_csv(all_urls_page)
    batch_size = 40000  # Размер каждой порции URL
    # Разделяем список urls на подсписки по batch_size
    for i in range(0, len(urls), batch_size):
        url_batch = urls[i : i + batch_size]  # Берем следующую порцию до 50 000
        for url in url_batch:
            # Формирование имени файла
            url_parts = url.split("/")
            last_part = url_parts[-1].split("?")  # Разделяем последний сегмент по '?'

            # Основная часть имени
            base_name = "_".join(
                part.replace("-", "_") for part in url_parts[-3:-1]
            )  # Берем последние три части (без query string)

            # Обработка query string (если есть)
            if len(last_part) > 1:
                query_part = last_part[1].replace("=", "_").replace("-", "_")
                file_name = (
                    f"{base_name}_{last_part[0].replace('-', '_')}_{query_part}.html"
                )
            else:
                file_name = f"{base_name}_{last_part[0].replace('-', '_')}.html"

            html_output_file = html_directory / file_name
            # Если файл HTML уже существует, удаляем JSON файл и пропускаем
            if html_output_file.exists():
                # logger.warning(
                #     f"Файл {html_company} уже существует, пропускаем.")
                continue
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
            response = requests.post(
                url="https://async.scraperapi.com/jobs",
                json={
                    "apiKey": api_key,
                    "url": url,
                    "keep_headers": "true",
                    "device_type": "desktop",
                    "headers": headers,
                },
                timeout=30,
            )
            if response.status_code == 200:
                response_data = response.json()
                job_id = response_data.get("id")
                json_file = json_directory / f"{job_id}.json"
                with open(json_file, "w", encoding="utf-8") as file:
                    json.dump(response_data, file, indent=4)
                logger.info(f"Задача отправлена для URL {url}")
                # logger.info(
                #     f"Задача отправлена для URL {url}, статус доступен по адресу: {response_data.get('statusUrl')}"
                # )
            else:
                logger.error(
                    f"Ошибка при отправке задачи для URL {url}: {response.status_code}"
                )


def parsing_html():
    """
    Обрабатывает HTML-файлы в указанной директории, извлекает данные из тегов, сохраняет в файл JSON.
    """
    output_file = Path("extracted_profile_data.json")
    extracted_data = {
        "project": "doctolib.de",
        "data": [],  # Список для хранения словарей
    }

    # Проверяем, существует ли директория
    if not html_directory.is_dir():
        logger.error(f"Директория {html_directory} не существует.")
        return

    for html_file in html_directory.glob("*.html"):
        try:
            with html_file.open(encoding="utf-8") as file:
                logger.info(html_file)
                description = None
                clinic_name = None
                address = None
                latitude = None
                longitude = None
                languages = None
                dl_transport = None
                dl_profile_bio = None
                href = None
                content = file.read()
                soup = BeautifulSoup(content, "lxml")
                script_tags = soup.find("script", {"type": "application/ld+json"})
                ld_json = json.loads(script_tags.string.strip())
                # logger.info(ld_json)
                # Извлекаем данные
                title = soup.find("h1", {"id": "profile-name-with-title"})
                if not title:
                    all_data = {"notPresent": True}
                    data_doctor = soup.find("div", {"id": "js-directory-doctor-page"})
                    if data_doctor:
                        # Извлекаем JSON из атрибута "data-props"
                        raw_json_data = data_doctor.get("data-props")

                        try:
                            # Парсим JSON из строки
                            parsed_data = json.loads(raw_json_data)

                            # Извлекаем необходимые данные
                            all_data["title"] = parsed_data.get("fullName")
                            all_data["speciality"] = parsed_data.get("speciality")

                            doctor_place = parsed_data.get("doctorPlace", {})
                            # all_data["address"] = doctor_place.get("address")
                            # all_data["zipcode"] = doctor_place.get("zipcode")
                            # all_data["city"] = doctor_place.get("city")
                            all_data["landline_number"] = doctor_place.get(
                                "landline_number"
                            )

                            all_data["address"] = (
                                f"{doctor_place.get('address')}, {doctor_place.get('zipcode')}{doctor_place.get('city')}"
                            )
                            extracted_data["data"].append(all_data)
                            continue
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка декодирования JSON: {e}")
                            all_data["error"] = "Ошибка декодирования JSON"
                    else:
                        logger.warning(
                            f"Элемент с id 'js-directory-doctor-page' не найден {html_file}"
                        )
                        all_data["error"] = "Элемент не найден"
                speciality = soup.find("div", {"class": "dl-profile-header-speciality"})

                specialities = None
                if speciality:
                    # Извлекаем все элементы <span> внутри блока
                    spans = speciality.find_all("span")
                    # Объединяем текст из всех <span> в одну строку
                    raw_text = " ".join(span.text.strip() for span in spans)
                    # Разделяем строку по запятым и "und"
                    specialities = [
                        spec.strip()
                        for spec in raw_text.replace(" und ", ", ").split(",")
                    ]
                else:
                    specialities = None

                dl_profile = soup.find("div", {"class": "dl-profile-text"})
                insurance_types = None
                if dl_profile:
                    raw_text = dl_profile.text.strip()
                    # Разделяем строку по ключевым словам "und", "sowie"
                    insurance_types = [
                        item.strip()
                        for item in raw_text.replace(" sowie ", ", ")
                        .replace(" und ", ", ")
                        .split(",")
                    ]
                dl_profile_skills = soup.find("div", {"class": "dl-profile-skills"})

                # Обрабатываем навыки
                skills = []
                if dl_profile_skills:
                    profile_skill_raw = dl_profile_skills.find_all(
                        "div", {"class": "dl-profile-skill-chip"}
                    )
                    for skill_raw in profile_skill_raw:
                        if skill_raw:
                            skills.append(skill_raw.text.strip())
                image_profile = ld_json.get("image", None)
                image_profile = f"https:{image_profile}"

                dl_profile_practice_transport = soup.select_one(
                    "#main-content > div.dl-profile-bg.dl-profile > div.dl-profile-wrapper.dl-profile-responsive-wrapper.dl-profile-wrapper-gap > div.dl-profile-body-wrapper.mt-8 > div:nth-child(8) > div > div.dl-profile-card-content > div:nth-child(3)"
                )
                # Извлекаем текст всех элементов <span>
                dl_transport = []
                if dl_profile_practice_transport:
                    spans = dl_profile_practice_transport.find_all("span")
                    dl_transport = [span.text.strip() for span in spans]

                practice_map_div = soup.find("div", {"class": "js-maps-doctor-map"})
                if practice_map_div:
                    data_props = practice_map_div.get("data-props")

                    if data_props:
                        # Парсим data-props как JSON
                        practice_data = json.loads(data_props)
                        address = practice_data.get("fullAddress")
                        latitude = practice_data.get("lat")
                        longitude = practice_data.get("lng")
                dl_profile_title_raw = soup.find(
                    "h2",
                    {
                        "class": "dl-profile-card-title dl-text dl-text-title dl-text-bold dl-text-s dl-text-neutral-150"
                    },
                )
                dl_profile_title = (
                    dl_profile_title_raw.text.strip() if dl_profile_title_raw else None
                )

                # Извлекаем описание
                dl_profile_bio_raw = soup.find(
                    "p", {"class": "dl-profile-text js-bio dl-profile-bio"}
                )
                dl_profile_bio = (
                    dl_profile_bio_raw.text.strip() if dl_profile_bio_raw else None
                )

                # Формируем результат
                if dl_profile_title and dl_profile_bio:
                    description = {
                        "title": "Profil",
                        "Herzlich willkommen": dl_profile_bio,
                    }
                    # logger.info(description)
                else:
                    description = None
                    # logger.error(html_file)
                    # logger.warning("Данные профиля отсутствуют.")

                language_section = soup.select_one(
                    ".dl-profile-row-section h3.dl-profile-card-subtitle"
                )

                languages = []
                if language_section and "Gesprochene Sprachen" in language_section.text:
                    # Ищем текст внутри родительского <div>
                    parent_div = language_section.find_parent()
                    if parent_div:
                        # Извлекаем текст, удаляем заголовок и разделяем по "und" и пробелам
                        raw_languages = parent_div.text.replace(
                            "Gesprochene Sprachen", ""
                        ).strip()
                        languages = [
                            lang.strip() for lang in raw_languages.split(" und ")
                        ]
                else:
                    languages = None
                    # logger.warning("Раздел 'Gesprochene Sprachen' не найден.")
                dl_profile_history_raw = soup.find_all(
                    "div", {"class": "dl-profile-card-section dl-profile-history"}
                )
                history_data = []
                for history in dl_profile_history_raw:
                    section_title = (
                        history.find("h3").get_text(strip=True)
                        if history.find("h3")
                        else "Без заголовка"
                    )
                    section_text = history.get_text(strip=True, separator="\n")
                    history_data.append(
                        {"title": section_title, "content": section_text}
                    )
                openingHours = ld_json.get("openingHours", [])
                phone_number = ld_json.get("telephone", None)
                clinic_name_raw = soup.find(
                    "div", {"class": "dl-profile-practice-name"}
                )
                if clinic_name_raw:
                    clinic_name = clinic_name_raw.text.strip()
                # Ищем элемент с заголовком "Website"
                website_section = soup.find("h3", string="Website")

                # Проверяем, нашли ли элемент
                if website_section:
                    # Переходим к родительскому блоку и ищем ссылку
                    link = website_section.find_next("a", href=True)
                    if link:
                        href = link["href"]

                # Сохраняем данные
                all_data = {
                    "title": title.text.strip() if title else None,
                    "services": skills,
                    "image_profile": image_profile,
                    "website_section": href,
                    "dl_language": languages,
                }
                all_data["specialities"] = specialities
                all_data["insurance"] = insurance_types
                all_data["transport"] = dl_transport
                all_data["description"] = description
                all_data["history_data"] = history_data
                polyclinic_data = {
                    "polyclinics": [
                        {
                            "phone_number": [phone_number],
                            "clinic_name": clinic_name,
                            "address": address,
                            "opening_hours": openingHours,
                            "gps": [{"lat": latitude, "lng": longitude}],
                            "offered_services": None,
                        }
                    ]
                }
                # Добавляем данные polyclinics в all_data
                all_data.update(polyclinic_data)

                # Добавляем all_data в список
                extracted_data["data"].append(all_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")
    # logger.info(extracted_data)
    # Сохраняем данные в файл JSON
    try:
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        # logger.info(f"Все данные сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {output_file}: {e}")


if __name__ == "__main__":

    # get_sitemap_start()
    # parsing_start_sitemap()
    # get_sitemap_all()
    # extract_urls_from_xml_files()
    # asyncio.run(main_url())
    parsing_html()
