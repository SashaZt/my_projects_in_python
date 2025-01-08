import asyncio
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from playwright.async_api import async_playwright

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
configuration_directory = current_directory / "configuration"
html_page_directory = current_directory / "html_page"
data_directory = current_directory / "data"

configuration_directory.mkdir(parents=True, exist_ok=True)
html_page_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)


async def main():
    async with async_playwright() as playwright:
        # Запускаем браузер
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        # Создаем новую страницу
        page = await context.new_page()

        # Переходим по URL
        await page.goto("https://www.merx.com/")

        # Ждем полной загрузки страницы
        await page.wait_for_load_state("networkidle")

        # Находим ссылку на кнопку "Login" и нажимаем её
        await page.click("a.mets-command-button.loginButton#header_btnLogin")

        # Ждем полной загрузки страницы после нажатия кнопки
        await page.wait_for_load_state("networkidle")

        # Находим поле для ввода логина и вводим значение
        await page.fill("input#j_username", "max@mldrl.com")

        # Находим поле для ввода пароля и вводим значение
        await page.fill("input#j_password", "MERx(6379)")

        # Находим кнопку "Login" и нажимаем её
        await page.click("button#loginButton")

        # Ждем 60 секунд
        await asyncio.sleep(30)

        # Циклически переходим по страницам
        while True:
            # Прокручиваем страницу до самого низа
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # Ждем, пока появится блок навигации
            navigation_div = await page.query_selector("div.mets-page-navigation")
            if navigation_div:

                # Извлекаем номер текущей страницы
                selected_span = await navigation_div.query_selector("span.selected")
                if selected_span:
                    number_page = await selected_span.text_content()
                    print(f"Current page number: {number_page}")

                # Проверяем наличие кнопки "Go to Next Page"
                next_page_link = await navigation_div.query_selector(
                    'a.next[title="Go to Next Page "]'
                )
                if next_page_link:
                    # Нажимаем на кнопку "Go to Next Page"
                    await next_page_link.click()

                    # Делаем паузу 5 секунд
                    await asyncio.sleep(5)

                    # Сохраняем контент страницы в HTML файл
                    content = await page.content()
                    with open(
                        f"page_{number_page}.html", "w", encoding="utf-8"
                    ) as file:
                        file.write(content)
                else:
                    # Если кнопки "Next Page" нет, выходим из цикла
                    break
            else:
                # Если блока навигации нет, выходим из цикла
                break

        # Закрываем браузер
        await browser.close()


def get_url():

    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    for html_file in html_page_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            # Найти таблицу с id "solicitationsTable"
            table = soup.find("table", {"id": "solicitationsTable"})
            if not table:
                print(f"Table with id 'solicitationsTable' not found in {html_file}")
                continue

            # Находим все ссылки с классом "solicitationsTitleLink mets-command-link"
            links_raw = table.find_all(
                "a", {"class": "solicitationsTitleLink mets-command-link"}
            )
            for link in links_raw:
                if "href" in link.attrs:
                    full_url = f"https://www.merx.com{link['href']}"
                    unique_itm_values.add(full_url)

    # Создаем DataFrame и сохраняем в CSV
    df = pd.DataFrame({"url": list(unique_itm_values)})
    output_file = "output.csv"
    df.to_csv(output_file, index=False)
    print(f"Extracted {len(unique_itm_values)} unique links and saved to {output_file}")


def read_csv_to_list():
    """
    Reads a CSV file with a column named 'url' and returns a list of URLs.

    :param file_path: Path to the CSV file.
    :return: List of URLs from the 'url' column.
    """
    try:
        output_file = "output.csv"
        # Читаем CSV файл
        df = pd.read_csv(output_file)

        # Проверяем, содержит ли файл столбец 'url'
        if "url" not in df.columns:
            raise ValueError("The CSV file does not contain a 'url' column.")

        # Преобразуем столбец 'url' в список
        url_list = df["url"].dropna().tolist()
        return url_list

    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return []


def extract_id(url):
    """
    Extracts the numeric ID from the given URL.

    :param url: The URL string to extract the ID from.
    :return: The extracted numeric ID as a string, or None if not found.
    """
    match = re.search(r"/(\d+)(?:\?|$)", url)
    return match.group(1) if match else None


def is_file_missing(directory_path, file_name):
    """
    Проверяет, существует ли указанный файл в директории.

    :param directory_path: Путь к директории (Path объект или строка).
    :param file_name: Имя файла для проверки.
    :return: True, если файл отсутствует, иначе False.
    """
    directory = Path(directory_path)
    return not (directory / file_name).exists()


def has_required_files(directory_path, required_count):
    """
    Проверяет, существует ли директория и содержит ли она указанное количество файлов.

    :param directory_path: Путь к директории (Path объект или строка).
    :param required_count: Необходимое количество файлов в директории.
    :return: True, если директория существует и содержит указанное количество файлов, иначе False.
    """
    directory = Path(directory_path)
    if directory.exists() and directory.is_dir():
        return len(list(directory.glob("*.html"))) >= required_count
    return False


def load_urls(file_path):
    """
    Загружает список URL из CSV файла.

    :param file_path: Путь к файлу CSV.
    :return: Список URL.
    """
    file = Path(file_path)
    if file.exists():
        df = pd.read_csv(file)
        return df["url"].dropna().tolist()
    return []


def save_url(file_path, url):
    """
    Добавляет URL в CSV файл.

    :param file_path: Путь к файлу CSV.
    :param url: URL для добавления.
    """
    file = Path(file_path)
    if file.exists():
        df = pd.read_csv(file)
        urls = df["url"].tolist()
        if url not in urls:
            urls.append(url)
            df = pd.DataFrame({"url": urls})
            df.to_csv(file_path, index=False)
    else:
        df = pd.DataFrame({"url": [url]})
        df.to_csv(file_path, index=False)


async def get_tenders():
    async with async_playwright() as playwright:
        # Запускаем браузер
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        while True:
            # Создаем новую страницу
            page = await context.new_page()

            # Переходим по URL
            await page.goto("https://www.merx.com/")

            # Ждем полной загрузки страницы
            await page.wait_for_load_state("networkidle")

            # Находим ссылку на кнопку "Login" и нажимаем её
            await page.click("a.mets-command-button.loginButton#header_btnLogin")

            # Ждем полной загрузки страницы после нажатия кнопки
            await page.wait_for_load_state("networkidle")

            # Находим поле для ввода логина и вводим значение
            await page.fill("input#j_username", "max@mldrl.com")

            # Находим поле для ввода пароля и вводим значение
            await page.fill("input#j_password", "MERx(6379)")

            # Нажимаем кнопку "Login"
            await page.click("button#loginButton")

            # Проверяем наличие сообщения об ошибке
            error_message_selector = "div.message-panel-content > p"
            try:
                await page.wait_for_selector(error_message_selector, timeout=5000)
                error_message = await page.inner_text(error_message_selector)
                if "The account provided is currently in use" in error_message:
                    logger.info(
                        "Account in use. Waiting for 10 minutes before retrying..."
                    )
                    await asyncio.sleep(600)  # Пауза 10 минут
                else:
                    logger.error("Unexpected error: Exiting.")
                    break
            except Exception:
                logger.info("Login successful.")
                break

        # Ждем 2 секунды после успешного входа
        await asyncio.sleep(2)
        all_urls = load_urls("output.csv")
        completed_urls_file = "completed_urls.csv"  # Здесь строка, а не список
        completed_urls = load_urls(completed_urls_file)

        urls_to_process = [url for url in all_urls if url not in completed_urls]
        for url in urls_to_process:
            id_url = extract_id(url)
            id_url_directory = data_directory / id_url
            if has_required_files(id_url_directory, 5):
                logger.info(
                    f"Skipping {url}, directory {id_url_directory} already has 5 files."
                )
                save_url(completed_urls_file, url)
                continue

            id_url_directory.mkdir(parents=True, exist_ok=True)
            await page.goto(url)
            file_name = id_url_directory / "page_Notice.html"
            content = await page.content()
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(content)
            logger.info("Ищем tab_view")
            # Находим основной блок с вкладками
            tab_view = await page.query_selector("//ul[@id='innerTabView']")
            if not tab_view:
                logger.error("Tab view not found. Skipping URL.")
                continue
            logger.info("Есть tab_view")
            await asyncio.sleep(10)  # Пауза 10 сек
            # Находим только нужные вкладки внутри tab_view
            titles_to_click = [
                "Categories",
                "Bid Results",
                "Award",
                "List of suppliers who have downloaded documents",
            ]

            all_titles_completed = True

            for title in titles_to_click:
                logger.info(title)
                title_element = await tab_view.query_selector(f'a[title="{title}"]')
                await asyncio.sleep(1)  # Пауза 10 сек
                if title_element:
                    logger.info(f"Элемент есть {title}")
                    file_name = (
                        f"page_{title.replace(' ', '_').replace('&', 'and')}.html"
                    )
                    file_path = id_url_directory / file_name

                    if not file_path.exists():
                        logger.info(f"Нажимаем {title}")
                        await title_element.click()
                        await page.wait_for_load_state("networkidle")
                        logger.info(f"Сохраняем в {file_path}")
                        # Сохраняем контент страницы в файл
                        content = await page.content()
                        with open(file_path, "w", encoding="utf-8") as file:
                            file.write(content)
                    else:
                        logger.info(f"Файл есть {file_path}")
                else:
                    all_titles_completed = False
                    print(f"Title '{title}' not found. Skipping.")

            # Записываем URL в файл после завершения обработки
            if all_titles_completed:
                save_url(completed_urls_file, url)

        await browser.close()


if __name__ == "__main__":
    # Запускаем асинхронный код
    # asyncio.run(main())
    # get_url()

    asyncio.run(get_tenders())
