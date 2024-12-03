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
            # "ultra_premium": "true",
        }
        retries = 0
        file_name = f"{url.split('/')[-2]}_{url.split('/')[-1]}"
        sitemap_output_file = xml_files_directory / file_name
        if sitemap_output_file.exists():
            continue
        while True:
            try:

                r = requests.get(
                    "https://api.scraperapi.com/", params=payload, timeout=60
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

            response = requests.post(
                url="https://async.scraperapi.com/jobs",
                json={"apiKey": api_key, "url": url},
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
    extracted_data = []

    # Проверяем, существует ли директория
    if not html_directory.is_dir():
        logger.error(f"Директория {html_directory} не существует.")
        return

    for html_file in html_directory.glob("*.html"):
        try:
            with html_file.open(encoding="utf-8") as file:
                content = file.read()
                soup = BeautifulSoup(content, "lxml")

                # Извлекаем данные
                title = soup.find("h1", {"id": "profile-name-with-title"})
                speciality = soup.find("div", {"class": "dl-profile-header-speciality"})
                dl_profile = soup.find("div", {"class": "dl-profile-text"})
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
                skills = ", ".join(skills)  # Преобразуем список в строку

                # Сохраняем данные
                all_data = {
                    "title": title.text.strip() if title else None,
                    "speciality": speciality.text.strip() if speciality else None,
                    "dl_profile": dl_profile.text.strip() if dl_profile else None,
                    "skills": skills if skills else None,
                }
                extracted_data.append(all_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")

    # Сохраняем данные в файл JSON
    try:
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Все данные сохранены в {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в файл {output_file}: {e}")


if __name__ == "__main__":

    # get_sitemap_start()
    # parsing_start_sitemap()
    # get_sitemap_all()
    # extract_urls_from_xml_files()
    # asyncio.run(main_url())
    parsing_html()
