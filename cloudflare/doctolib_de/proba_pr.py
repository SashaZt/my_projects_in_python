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


async def main():
    # -------- ПРОКСИ -------- #
    proxies = load_proxies()
    if proxies:
        for proxy in proxies:
            proxy_data = parse_proxy(proxy)
            browser = await uc.start(
                browser_args=[f"--proxy-server={proxy_data['server']}"]
            )
            main_tab = await browser.get("draft:,")
            await setup_proxy(proxy_data, main_tab)
            ip_page = await browser.get("https://www.myexternalip.com/raw")
            await asyncio.sleep(2)
            ip = await ip_page.evaluate("document.body.textContent.trim()")
            print(f">= IP Address: {ip}")
    else:
        # Без прокси
        browser = await uc.start()
        main_tab = await browser.get("draft:,")
        ip_page = await browser.get("https://www.myexternalip.com/raw")
        await asyncio.sleep(2)
        ip = await ip_page.evaluate("document.body.textContent.trim()")
        print(f">= IP Address: {ip}")
    # -------- ПРОКСИ -------- #


# Запуск основной функции
asyncio.run(main())
