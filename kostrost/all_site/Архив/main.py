import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from excel_extractor import extract_column_a_from_excel
from kostrost.all_site.config.logger import logger
from kostrost.all_site.scraper_api_async import ScraperAPI

# Константы
API_KEY = "d415ddc01cf23948eff76e4447f69372"
BASE_HTML_DIR = "html_pages"
MAX_WORKERS = 5  # Количество параллельных запросов
DELAY_BETWEEN_REQUESTS = 1  # Пауза между запросами в секундах


def ensure_directory_exists(directory_path):
    """Создает директорию, если она не существует"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Создана директория: {directory_path}")


def download_html(url, output_path):
    """
    Скачивает HTML страницу через scraperapi и сохраняет в указанный файл
    """
    scraper = ScraperAPI(
        API_KEY, max_retries=3, delay_between_requests=DELAY_BETWEEN_REQUESTS
    )
    logger.info(f"Скачивание: {url}")

    html_content = scraper.download_html(url)

    if html_content:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        logger.info(f"Сохранено в: {output_path}")
        return True

    logger.error(f"Не удалось скачать {url}")
    return False


def download_url_task(task_data):
    """Задача для скачивания одного URL (используется в ThreadPoolExecutor)"""
    sheet_name, url, index, base_dir = task_data

    sheet_dir = os.path.join(base_dir, sheet_name)
    ensure_directory_exists(sheet_dir)

    # Создаем имя файла на основе индекса и URL
    filename = f"{index+1}_{url.split('/')[-1]}.html"
    if len(filename) > 100:  # Ограничиваем длину имени файла
        filename = f"{index+1}_{filename[:90]}.html"

    file_path = os.path.join(sheet_dir, filename)

    # Если файл уже существует, пропускаем
    if os.path.exists(file_path):
        return sheet_name, True, f"Файл уже существует: {file_path}"

    # Скачиваем HTML
    success = download_html(url, file_path)
    return sheet_name, success, url


def process_sheet_data(sheet_name, urls_data, use_threading=True):
    """Обрабатывает данные одного листа: создает папку и скачивает все URL"""
    sheet_dir = os.path.join(BASE_HTML_DIR, sheet_name)
    ensure_directory_exists(sheet_dir)

    tasks = []
    for i, url_item in enumerate(urls_data):
        url = url_item.get("url")
        if not url:
            continue

        tasks.append((sheet_name, url, i, BASE_HTML_DIR))

    success_count = 0

    if use_threading and len(tasks) > 1:
        # Используем параллельное скачивание
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tasks))) as executor:
            results = list(executor.map(download_url_task, tasks))

            for sheet_name, success, url in results:
                if success:
                    success_count += 1
    else:
        # Последовательное скачивание
        for task in tasks:
            sheet_name, success, url = download_url_task(task)
            if success:
                success_count += 1
            time.sleep(DELAY_BETWEEN_REQUESTS)

    logger.info(
        f"Лист {sheet_name}: загружено {success_count} из {len(urls_data)} страниц"
    )
    return success_count


def download_all_pages(extracted_data, use_threading=True):
    """Скачивает все страницы из извлеченных данных"""
    # Создаем основную директорию для HTML-файлов
    ensure_directory_exists(BASE_HTML_DIR)

    total_urls = sum(
        len(sheet_data[sheet_name])
        for sheet_data in extracted_data
        for sheet_name in sheet_data
    )
    logger.info(
        f"Начинаем скачивание {total_urls} URL-адресов из {len(extracted_data)} листов..."
    )

    total_success = 0

    # Обрабатываем каждый лист последовательно
    for sheet_data in extracted_data:
        for sheet_name, urls_data in sheet_data.items():
            success_count = process_sheet_data(sheet_name, urls_data, use_threading)
            total_success += success_count

    logger.info(
        f"Скачивание завершено. Успешно загружено {total_success} из {total_urls} страниц."
    )
    return total_success


def main():
    # # Путь к Excel-файлу где все листы и все ссылки
    # excel_file_path = "thomann.xlsx"

    # # Извлекаем данные из Excel
    # logger.info(f"Извлечение данных из {excel_file_path}...")
    # extracted_data = extract_column_a_from_excel(excel_file_path)

    # # Сохраняем извлеченные данные в JSON
    # with open("extracted_urls.json", "w", encoding="utf-8") as f:
    #     json.dump(extracted_data, f, indent=4, ensure_ascii=False)
    # logger.info(f"Данные сохранены в extracted_urls.json")

    # Собрал по одной ссылки с каждого листа
    with open("test_one_url.json", "r", encoding="utf-8") as f:
        extracted_data = json.load(f)
    # Подсчитываем общее количество URL
    total_urls = sum(
        len(sheet_data[sheet_name])
        for sheet_data in extracted_data
        for sheet_name in sheet_data
    )
    logger.info(
        f"Всего найдено {total_urls} URL-адресов в {len(extracted_data)} листах"
    )

    # Запрашиваем подтверждение перед скачиванием
    confirm = input(f"Начать скачивание {total_urls} страниц? (y/n): ")
    if confirm.lower() != "y":
        logger.error("Скачивание отменено.")
        return

    # Запрашиваем режим скачивания
    threading_mode = input(
        "Использовать многопоточное скачивание? (y/n, по умолчанию y): "
    )
    use_threading = threading_mode.lower() != "n"

    # Скачиваем все страницы
    download_all_pages(extracted_data, use_threading)


if __name__ == "__main__":
    main()
