import nodriver as uc
from nodriver.cdp import fetch
import pandas as pd
import xml.etree.ElementTree as ET
import asyncio
import json
from pathlib import Path
import pandas as pd
from configuration.logger_setup import logger
import os

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_file_directory = current_directory / "xml_file"
xml_files_directory = current_directory / "xml_files"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
xml_file_directory.mkdir(exist_ok=True, parents=True)
xml_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"
sitemap_output_file = xml_file_directory / "sitemap.xml"
start_sitemap_output_file = current_directory / "start_sitemap.csv"
all_urls_output_file = data_directory / "all_urls.csv"


# Функция загрузки списка прокси
def load_proxies():
    if os.path.exists(file_proxy):
        with open(file_proxy, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies
    else:
        logger.warning(
            "Файл с прокси не найден. Работа будет выполнена локально без прокси."
        )
        return []


# Функция для парсинга прокси
def parse_proxy(proxy):
    if "@" in proxy:
        protocol, rest = proxy.split("://", 1)
        credentials, server = rest.split("@", 1)
        username, password = credentials.split(":", 1)
        return {
            "server": f"{protocol}://{server}",
            "username": username,
            "password": password,
        }
    else:
        return {"server": f"http://{proxy}"}


async def setup_proxy(proxy_data, tab):
    async def auth_challenge_handler(event: fetch.AuthRequired):
        # Ответ на запрос аутентификации
        await tab.send(
            fetch.continue_with_auth(
                request_id=event.request_id,
                auth_challenge_response=fetch.AuthChallengeResponse(
                    response="ProvideCredentials",
                    username=proxy_data.get("username"),
                    password=proxy_data.get("password"),
                ),
            )
        )

    async def req_paused(event: fetch.RequestPaused):
        # Продолжение запроса
        await tab.send(fetch.continue_request(request_id=event.request_id))

    # Добавление обработчиков для событий fetch
    tab.add_handler(
        fetch.RequestPaused, lambda event: asyncio.create_task(req_paused(event))
    )
    tab.add_handler(
        fetch.AuthRequired,
        lambda event: asyncio.create_task(auth_challenge_handler(event)),
    )

    # Включение домена fetch с обработкой запросов аутентификации
    await tab.send(fetch.enable(handle_auth_requests=True))


# Получаем первый, стартовый sitemap
async def get_sitemap():
    # Открываем браузер
    browser = (
        await uc.start()
    )  # Добавьте параметр headless=True, если не хотите видеть браузер
    # Переходим на страницу
    page = await browser.get("https://www.doctolib.de/sitemap.xml")
    await asyncio.sleep(1)
    content = await page.get_content()

    # Проверяем, что содержимое не None
    if content:
        # Сохраняем в файл sitemap.xml
        with open(sitemap_output_file, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        logger.error("Контент не найден.")

    # Закрываем страницу
    await page.close()


# Парсим первый стартовый sitemap
def parsing_start_sitemap():
    url = "https://www.doctolib.de/psychotherapeut-psychotherapeutin/rees/anke-sievert-minor"
    file_name = f"{url.split('/')[-3].replace("-","_")}_{url.split('/')[-2].replace("-","_")}_{url.split('/')[-1].replace("-","_")}"
    logger.info(file_name)
    exit()
    # Открываем файл sitemap.xml
    tree = ET.parse(sitemap_output_file)
    root = tree.getroot()

    # Собираем все URL из XML
    namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [elem.text.strip() for elem in root.findall(".//ns:loc", namespaces)]

    # Записываем в start_sitemap.csv
    df = pd.DataFrame({"url": urls})
    df.to_csv(start_sitemap_output_file, index=False)


def read_csv(file):
    # Читаем файл start_sitemap.csv и возвращаем список URL
    df = pd.read_csv(file)
    return df["url"].tolist()


# По ссылкам получаем все sitemap
async def get_all_sitemap():
    urls = read_csv(start_sitemap_output_file)
    # Открываем браузер
    browser = (
        await uc.start()
    )  # Добавьте параметр headless=True, если не хотите видеть браузер
    # Переходим на страницу
    for url in urls:
        file_name = f"{url.split('/')[-2]}_{url.split('/')[-1]}"
        sitemap_output_file = xml_files_directory / file_name
        page = await browser.get(url)
        await asyncio.sleep(1)
        content = await page.get_content()

        # Проверяем, что содержимое не None
        if content:
            # Сохраняем в файл sitemap.xml
            with open(sitemap_output_file, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            logger.error("Контент не найден.")

    # Закрываем страницу
    await page.close()


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
    df.to_csv(all_urls_output_file, index=False)


async def get_all_urls():

    urls = read_csv(all_urls_output_file)
    browser = await uc.start(
        browser_args=[f"--proxy-server={'185.112.13.176:2831'}"],
    )  # Добавьте параметр headless=True, если не хотите видеть браузер

    # Переходим на страницу
    for url in urls[:1]:
        file_name = f"{url.split('/')[-3].replace("-","_")}_{url.split('/')[-2].replace("-","_")}_{url.split('/')[-1].replace("-","_")}"
        sitemap_output_file = xml_files_directory / file_name
        url = "https://www.doctolib.de/radiologie-diagnostische/berlin/christian-enzweiler?pid=practice-9707"
        main_tab = await browser.get(url)
        await setup_fetch_intercept(main_tab)
        await asyncio.sleep(20)
        intercepted_url = await setup_fetch_intercept(main_tab)
        if intercepted_url:
            logger.info(f"Переход на перехваченный URL: {intercepted_url}")
            await main_tab.goto(intercepted_url)
        # content = await page.get_content()

        # # Проверяем, что содержимое не None
        # if content:
        #     # Сохраняем в файл sitemap.xml
        #     with open(sitemap_output_file, "w", encoding="utf-8") as f:
        #         f.write(content)
        # else:
        #     logger.error("Контент не найден.")

    # Закрываем страницу
    # await page.close()


async def setup_fetch_intercept(tab):
    intercepted_url = None

    async def req_paused(event: fetch.RequestPaused):
        nonlocal intercepted_url
        logger.info(f"Запрос приостановлен: {event.request.url}")
        if (
            "doctolib.de/online_booking/api/slot_selection_funnel/v1/"
            in event.request.url
        ):
            intercepted_url = event.request.url
            await tab.send(fetch.continue_request(request_id=event.request_id))
        else:
            await tab.send(fetch.continue_request(request_id=event.request_id))

    tab.add_handler(
        fetch.RequestPaused, lambda event: asyncio.create_task(req_paused(event))
    )
    await tab.send(
        fetch.enable(
            patterns=[
                fetch.RequestPattern(
                    url_pattern="*doctolib.de/online_booking/api/slot_selection_funnel/v1/*",
                    request_stage=fetch.RequestStage.RESPONSE,
                )
            ],
            handle_auth_requests=True,
        )
    )
    await asyncio.sleep(2)  # Подождем, пока запрос будет перехвачен
    return intercepted_url


async def get_response_body(request_id, tab):
    try:
        response = await tab.send(fetch.get_response_body(request_id=request_id))
        logger.info(f"Тело ответа получено для ID запроса: {request_id}")
        return response.get("body") if response else None
    except Exception as e:
        logger.error(
            f"Не удалось получить тело ответа для ID запроса: {request_id}, ошибка: {e}"
        )
        return None


async def save_response_to_json(response_body):
    try:
        response_data = json.loads(response_body)
        with open("intercepted_responses.json", "a", encoding="utf-8") as json_file:
            json.dump(response_data, json_file, ensure_ascii=False, indent=4)
            json_file.write(",\n")
        logger.info("Тело ответа сохранено в intercepted_responses.json")
    except json.JSONDecodeError:
        logger.error("Не удалось декодировать JSON из тела ответа.")


if __name__ == "__main__":
    # uc.loop().run_until_complete(get_sitemap())
    # parsing_start_sitemap()
    # uc.loop().run_until_complete(get_all_sitemap())
    # extract_urls_from_xml_files()
    uc.loop().run_until_complete(get_all_urls())
