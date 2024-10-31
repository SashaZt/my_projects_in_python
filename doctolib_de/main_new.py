import nodriver as uc
from nodriver.cdp import fetch
import asyncio
import os
from configuration.logger_setup import logger
from pathlib import Path
import json

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
json_files_directory = current_directory / "json_files"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
json_files_directory.mkdir(exist_ok=True, parents=True)
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

    proxies = load_proxies()
    if proxies:
        for proxy in proxies[:1]:
            proxy_data = parse_proxy(proxy)
            logger.info(proxy_data)
            browser = await uc.start(
                browser_args=[f"--proxy-server={proxy_data['server']}"]
            )
            page = await browser.get("draft:,")
            await setup_proxy(proxy_data, page)

            url = "https://www.doctolib.de/radiologie-diagnostische/berlin/christian-enzweiler?pid=practice-9707"
            clinic = url.split("/")[-3].replace("-", "_")
            city = url.split("/")[-2]
            doctor = url.split("/")[-1].split("?")[0].replace("-", "_")
            html_doctor = html_files_directory / f"{clinic}_{city}_{doctor}.html"
            if html_doctor.exists():
                logger.warning(f"Файл {html_doctor} уже существует, пропускаем.")
                continue  # Переходим к следующей итерации цикла
            # Переходим на страницу

            page = await browser.get(url)
            element = await page.wait_for(
                selector="#profile-name-with-title", timeout=15
            )

            html_content = await page.get_content()
            with open(html_doctor, "w", encoding="utf-8") as file:
                file.write(html_content)

            # intercepted_url = await asyncio.wait_for(
            #     setup_fetch_intercept(main_tab), timeout=10.0
            # )
            # logger.info(f"Получили {intercepted_url}")
            # await save_html(proxy_data, intercepted_url, json_doctor)


async def save_html(proxy_data, url, json_doctor):
    browser = await uc.start(browser_args=[f"--proxy-server={proxy_data['server']}"])
    main_tab = await browser.get("draft:,")
    await setup_proxy(proxy_data, main_tab)
    main_tab = await browser.get(url)
    content = await main_tab.get_content()
    with open(json_doctor, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Сохраняем")


# РАБОЧИЙ КОД полностью
async def setup_fetch_intercept(tab):
    intercepted_url = asyncio.Future()
    # intercepted_request_id = asyncio.Future()

    async def req_paused(event: fetch.RequestPaused):
        logger.info(f"Запрос приостановлен: {event.request.url}")
        if (
            "doctolib.de/online_booking/api/slot_selection_funnel/v1/"
            in event.request.url
        ):
            intercepted_url.set_result(event.request.url)
            # intercepted_request_id.set_result(event.request_id)
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
    return await intercepted_url


if __name__ == "__main__":
    uc.loop().run_until_complete(get_all_urls())
