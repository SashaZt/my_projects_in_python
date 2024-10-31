import re
import asyncio
from playwright.async_api import async_playwright
import fitz  # PyMuPDF
import pandas as pd


async def get_browser(url):
    """
    Открывает страницу в браузере с указанным URL и возвращает объект страницы и браузер.
    """
    async with async_playwright() as p:
        # Запуск браузера и создание контекста с поддержкой загрузок
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)

        # Создаем новую вкладку
        page = await context.new_page()

        # Переходим по указанному URL
        try:
            await page.goto(url, timeout=60000, wait_until="networkidle")
        except Exception as e:
            print(f"Ошибка при переходе на {url}: {e}")
            await browser.close()
            return None, None  # Возвращаем None при ошибке

        return page, browser  # Возвращаем страницу и браузер


async def download_pdf(url):

    # Получаем объект страницы и браузер
    page, browser = await get_browser(url)
    await asyncio.sleep(5)  # Небольшая пауза

    # Извлекаем HTML контент страницы
    page_content = await page.content()
    match = re.search(r'var pdfUrl = "(.*?)";', page_content)

    if match:
        pdf_url = match.group(1).replace("\\/", "/")
        print(f"PDF URL найден: {pdf_url}")

        # Ожидаем загрузку файла
        async with page.expect_download() as download_info:
            await page.evaluate(
                f'window.open("{pdf_url}", "_blank")'
            )  # Открываем PDF в новой вкладке
        download = await download_info.value

        # Получаем путь к загруженному файлу
        download_path = await download.path()
        file_name = f"{pdf_url.split("/")[-3]}_{pdf_url.split("/")[-2]}_{pdf_url.split("/")[-1]}"
        # Перемещаем файл в текущую директорию
        # Сохраняем файл с нашим именем
        await download.save_as(f"./{file_name}.pdf")
        print(f"Файл успешно загружен: {file_name}.pdf")

    else:
        print("PDF URL не найден в HTML-коде страницы.")

    await browser.close()


def extract_email_from_pdf(pdf_path: str) -> str:
    # Открываем PDF-файл
    try:
        with fitz.open(pdf_path) as doc:
            # Извлекаем текст с первой страницы
            first_page = doc[0]
            text = first_page.get_text()

            # Паттерн для поиска email
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

            # Поиск email в тексте
            match = re.search(email_pattern, text)
            if match:
                return match.group(0)
            else:
                return "Email не найден на первой странице."
    except Exception as e:
        return f"Ошибка при обработке PDF: {str(e)}"


async def get_all_magazines():
    urls = [
        "https://ejournal.ipinternasional.com/index.php/jsh/issue/archive",
        "https://ejournal.ipinternasional.com/index.php/jostec/issue/archive",
        "https://ejournal.ipinternasional.com/index.php/ijcs/issue/archive",
        "https://ejournal.ipinternasional.com/index.php/ijere/issue/archive",
        "https://ejournal.ipinternasional.com/index.php/ijec/issue/archive",
        "https://ejournal.ipinternasional.com/index.php/ijphe/issue/archive",
    ]

    all_links = []  # Список для хранения всех ссылок

    for url in urls:
        # Получаем объект страницы и браузер
        page, browser = await get_browser(url)

        # Пропускаем URL, если браузер или страница не открылись
        if not page or not browser:
            continue
        await asyncio.sleep(5)  # Небольшая пауза
        # Ждем появления элемента с нужным селектором
        try:
            await page.wait_for_selector("#main-content > div", timeout=15000)
        except Exception as e:
            print(f"Ошибка при поиске селектора: {e}")
            await browser.close()
            return

        # Извлекаем все элементы <a class="title">
        title_links = await page.query_selector_all("div.media-body > h2 > a")

        # Список для хранения ссылок
        links = []

        # Извлекаем href из каждого элемента
        for link in title_links:
            href = await link.get_attribute("href")
            if href:
                links.append({"url": href})
                print(f"Найденная ссылка: {href}")

        # Закрываем браузер после завершения работы
        await browser.close()

    # Сохраняем все ссылки в CSV файл с помощью pandas
    output_file = "links.csv"
    df = pd.DataFrame(all_links)  # Создаем DataFrame
    df.to_csv(output_file, index=False)  # Сохраняем в CSV
    print(f"Ссылки сохранены в файл {output_file}")


if __name__ == "__main__":
    asyncio.run(get_all_magazines())
    # # Скачивание одного pdf
    # url = "https://ejournal.ipinternasional.com/index.php/ijphe/article/view/869/799"
    # asyncio.run(download_pdf(url))
    # # Получение email
    # pdf_name = "869_799_5874.pdf"
    # email = extract_email_from_pdf(pdf_name)
