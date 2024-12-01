import asyncio
from pathlib import Path

import aiofiles
from configuration.logger_setup import logger
from playwright.async_api import async_playwright

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
img_files_directory = current_directory / "img_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

# Создание директорий, если их нет
html_files_directory.mkdir(parents=True, exist_ok=True)
img_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
output_csv_file = data_directory / "output.csv"
xlsx_result = data_directory / "result.xlsx"
json_result = data_directory / "result.json"
file_proxy = configuration_directory / "proxy.txt"
config_txt_file = configuration_directory / "config.txt"


async def save_html_to_file(file_name: str, html_content: str):
    """
    Асинхронно сохраняет HTML-контент в файл.

    :param file_name: Имя файла для сохранения HTML-контента.
    :param html_content: HTML-контент, который нужно сохранить.
    """
    try:
        async with aiofiles.open(file_name, mode="w", encoding="utf-8") as file:
            await file.write(html_content)
        print(f"HTML-контент успешно сохранен в файл: {file_name}")
    except Exception as e:
        print(f"Ошибка при сохранении файла {file_name}: {e}")


async def extract_next_page_number(page):
    """
    Извлекает номер следующей страницы из атрибута href кнопки "Вперед".

    :param page: Объект страницы Playwright.
    :return: Номер следующей страницы (str) или None, если кнопка не найдена.
    """
    try:
        # Ищем элемент "Вперед"
        next_button = await page.query_selector('[data-qaid="next_page"]')
        if not next_button:
            print("Кнопка 'Вперед' не найдена.")
            return None

        # Получаем значение атрибута href
        href = await next_button.get_attribute("href")
        if href:
            # Извлекаем номер страницы из href
            page_number = href.split(";")[-1]
            print(f"Номер следующей страницы: {page_number}")
            return page_number
        else:
            print("Атрибут href отсутствует у кнопки 'Вперед'.")
            return None
    except Exception as e:
        print(f"Ошибка при извлечении номера страницы: {e}")
        return None


async def run(playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()

    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )

    url = "https://satu.kz/Dom-i-sad"

    await page.goto(url)
    url_id = url.rsplit("/", maxsplit=1)[-1].replace("-", "_")
    # Прокручиваем страницу вниз
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(5)  # Ждем, чтобы страница догрузилась
    first_page = 1
    first_html_file = html_files_directory / f"{url_id}_0{first_page}.html"
    html_content = await page.content()
    await save_html_to_file(first_html_file, html_content)
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(5)  # Ждем, чтобы страница догрузилась

        next_page_number = await extract_next_page_number(page)

        output_html_file = html_files_directory / f"{url_id}_0{next_page_number}.html"
        html_content = await page.content()
        await save_html_to_file(output_html_file, html_content)
        # Ищем кнопку "Вперед"
        try:
            next_button = await page.query_selector('[data-qaid="next_page"]')
            if next_button:
                print("Кнопка 'Вперед' найдена. Нажимаем...")
                await next_button.click()
                await page.wait_for_load_state("load")
                await asyncio.sleep(2)  # Ждем загрузки новой страницы
            else:
                print("Кнопка 'Вперед' не найдена. Завершаем...")
                break
        except Exception as e:
            print("Ошибка при поиске кнопки 'Вперед':", e)
            break

    await browser.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


# Запуск основной функции
asyncio.run(main())
