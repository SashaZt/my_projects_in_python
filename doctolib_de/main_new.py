import nodriver as uc
from nodriver.cdp import fetch
import asyncio
import os
from configuration.logger_setup import logger
from pathlib import Path

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"
csv_output_file = current_directory / "inn_data.csv"


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


async def get_all_urls():
    browser = await uc.start(
        browser_args=[f"--proxy-server={'185.112.13.176:2831'}"],
    )  # Добавьте параметр headless=True, если не хотите видеть браузер

    # Переходим на страницу
    url = "https://www.doctolib.de/radiologie-diagnostische/berlin/christian-enzweiler?pid=practice-9707"
    main_tab = await browser.get(url)
    await setup_fetch_intercept(main_tab)
    await asyncio.sleep(20)
    intercepted_url = await setup_fetch_intercept(main_tab)
    if intercepted_url:
        logger.info(f"Переход на перехваченный URL: {intercepted_url}")
        await main_tab.goto(intercepted_url)


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
    uc.loop().run_until_complete(get_all_urls())
