import nodriver as uc
from nodriver.cdp import fetch
import asyncio
import os
from configuration.logger_setup import logger
from pathlib import Path
import csv

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"
csv_output_file = data_directory / "all_urls.csv"


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


# Настройка прокси
async def setup_proxy(proxy_data, tab):
    async def auth_challenge_handler(event: fetch.AuthRequired):
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
        await tab.send(fetch.continue_request(request_id=event.request_id))

    tab.add_handler(
        fetch.RequestPaused, lambda event: asyncio.create_task(req_paused(event))
    )
    tab.add_handler(
        fetch.AuthRequired,
        lambda event: asyncio.create_task(auth_challenge_handler(event)),
    )
    await tab.send(fetch.enable(handle_auth_requests=True))


# Функция для загрузки одной страницы
async def single_html_one(url, browser):
    page = await browser.get(url)

    # Ожидание загрузки страницы через появление <body>
    try:
        await page.wait_for(selector="body", timeout=10)
    except asyncio.TimeoutError:
        logger.warning("Элемент <body> не загрузился в течение времени ожидания.")
    # Проверка на элемент с id "help_title" для возможной капчи
    try:
        element = await page.wait_for(selector="h1#help_title", timeout=1)
        if element:
            logger.info("Обнаружено сообщение проверки на робота. Ожидание 30 секунд.")
            await page.sleep(30)
    except asyncio.TimeoutError:
        pass
    html_content = await page.get_content()
    if "Retry later" in html_content:
        logger.error("Обнаружено сообщение 'Retry later'. Перезапускаем браузер.")
        raise RuntimeError("Сообщение 'Retry later' обнаружено. Перезапуск браузера.")

    html_content = await page.get_content()
    return html_content


# Основная функция для работы с URL-очередью
async def get_all_urls(url_queue, proxy_data=None):
    while not url_queue.empty():
        try:
            # Устанавливаем аргументы браузера (с прокси или без)
            browser_args = (
                [f"--proxy-server={proxy_data['server']}"] if proxy_data else []
            )
            browser = await uc.start(browser_args=browser_args)

            if proxy_data:
                page = await browser.get("draft:,")
                await setup_proxy(proxy_data, page)

            async with browser:
                while not url_queue.empty():
                    url = await url_queue.get()
                    parts = url.split("/")

                    if len(parts) < 4:
                        logger.warning(
                            f"URL {url} имеет недостаточно сегментов, пропускаем."
                        )
                        url_queue.task_done()
                        continue

                    clinic = parts[-3].replace("-", "_")
                    city = parts[-2]
                    doctor = parts[-1].split("?")[0].replace("-", "_")
                    html_doctor = (
                        html_files_directory / f"{clinic}_{city}_{doctor}.html"
                    )

                    if html_doctor.exists():
                        logger.warning(
                            f"Файл {html_doctor} уже существует, пропускаем."
                        )
                        url_queue.task_done()
                        continue

                    # Обработка URL
                    try:
                        html_content = await single_html_one(url, browser)
                        if html_content:
                            with open(html_doctor, "w", encoding="utf-8") as file:
                                file.write(html_content)
                            logger.info(f"Сохранена страница для {url}")
                    except RuntimeError as e:
                        # Обработка специального исключения для перезапуска браузера
                        logger.error(f"Необходим перезапуск браузера: {e}")
                        browser.stop()  # Принудительно завершить процесс браузера
                        break  # Выходим из внутреннего цикла для перезапуска браузера
                    except Exception as e:
                        logger.error(f"Ошибка при обработке {url}: {e}")
                    finally:
                        url_queue.task_done()

        except Exception as e:
            logger.error(f"Произошла ошибка в задаче: {e}")
            await asyncio.sleep(1)  # Небольшая пауза перед перезапуском


# Запуск пула задач
async def run_with_pool(max_workers=5):
    proxies = load_proxies()
    use_proxies = bool(proxies)
    if not use_proxies:
        logger.info("Работаем локально без прокси.")

    url_queue = asyncio.Queue()
    with open(csv_output_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            await url_queue.put(row[0])

    tasks = []
    if use_proxies:
        for proxy in proxies[:max_workers]:
            proxy_data = parse_proxy(proxy)
            tasks.append(asyncio.create_task(get_all_urls(url_queue, proxy_data)))
    else:
        for _ in range(max_workers):
            tasks.append(asyncio.create_task(get_all_urls(url_queue)))

    await asyncio.gather(*tasks)
    await url_queue.join()


if __name__ == "__main__":
    asyncio.run(run_with_pool())
