import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

from excel_extractor import extract_column_a_from_excel
from logger import logger
from scraper_api_async import ScraperAPIAsync

# Константы
API_KEY = "d415ddc01cf23948eff76e4447f69372"
BASE_HTML_DIR = "html_pages"
BATCH_SIZE = 10  # Количество URL в одном пакете
MAX_BATCHES = 3  # Максимальное количество одновременных пакетов


def ensure_directory_exists(directory_path):
    """Создает директорию, если она не существует"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.info(f"Создана директория: {directory_path}")


def process_url_batch(batch_data):
    """Обрабатывает один пакет URL-адресов"""
    urls_batch, output_dirs = batch_data

    logger.info(f"Обработка пакета из {len(urls_batch)} URL")

    # Создаем экземпляр асинхронного скрапера
    scraper = ScraperAPIAsync(API_KEY, max_retries=3, delay_between_requests=2)

    # Скачиваем пакет URL-адресов
    results = scraper.download_batch(urls_batch, output_dirs)

    # Подсчитываем успешные скачивания
    success_count = sum(1 for success in results.values() if success)
    logger.info(
        f"Пакет обработан: {success_count} из {len(urls_batch)} успешно скачаны"
    )

    return results


def prepare_batches(extracted_data):
    """
    Подготавливает пакеты URL-адресов для скачивания

    Returns:
        List of tuples (urls_batch, output_dirs)
    """
    all_batches = []
    current_batch_urls = []
    current_batch_dirs = {}

    # Проходим по всем листам и собираем URL-адреса в пакеты
    for sheet_data in extracted_data:
        for sheet_name, urls_data in sheet_data.items():
            # Создаем директорию для текущего листа
            sheet_dir = os.path.join(BASE_HTML_DIR, sheet_name)
            ensure_directory_exists(sheet_dir)

            # Добавляем URL-адреса в текущий пакет
            for url_item in urls_data:
                url = url_item.get("url")
                if not url:
                    continue

                # Формируем имя файла на основе URL
                url_parts = url.split("/")
                filename = url_parts[-1] if url_parts[-1] else "index"

                # Создаем имя для HTML-файла
                html_filename = f"{filename}.html"
                file_path = os.path.join(sheet_dir, html_filename)

                # Если файл уже существует, пропускаем
                if os.path.exists(file_path):
                    logger.info(f"Файл уже существует: {file_path}")
                    continue

                # Добавляем URL в текущий пакет
                current_batch_urls.append(url)
                current_batch_dirs[url] = sheet_dir

                # Если текущий пакет достиг максимального размера, сохраняем его
                if len(current_batch_urls) >= BATCH_SIZE:
                    all_batches.append(
                        (current_batch_urls.copy(), current_batch_dirs.copy())
                    )
                    current_batch_urls = []
                    current_batch_dirs = {}

    # Добавляем оставшиеся URL-адреса в последний пакет
    if current_batch_urls:
        all_batches.append((current_batch_urls, current_batch_dirs))

    return all_batches


def download_all_pages_async(extracted_data, use_threading=True):
    """Скачивает все страницы асинхронно"""
    # Создаем основную директорию для HTML-файлов
    ensure_directory_exists(BASE_HTML_DIR)

    # Подготавливаем пакеты URL-адресов
    batches = prepare_batches(extracted_data)

    total_urls = sum(len(batch[0]) for batch in batches)
    total_batches = len(batches)

    logger.info(
        f"Подготовлено {total_batches} пакетов с общим количеством {total_urls} URL-адресов"
    )

    # Обрабатываем пакеты
    total_success = 0

    if use_threading and total_batches > 1:
        # Параллельная обработка пакетов
        with ThreadPoolExecutor(
            max_workers=min(MAX_BATCHES, total_batches)
        ) as executor:
            results = list(executor.map(process_url_batch, batches))

            # Подсчитываем успешные скачивания
            for batch_results in results:
                for success in batch_results.values():
                    if success:
                        total_success += 1
    else:
        # Последовательная обработка пакетов
        for batch in batches:
            batch_results = process_url_batch(batch)

            for success in batch_results.values():
                if success:
                    total_success += 1

    logger.info(
        f"Скачивание завершено. Успешно загружено {total_success} из {total_urls} страниц."
    )
    return total_success


def main():
    # # Путь к Excel-файлу где все листы и все ссылки
    # excel_file_path = "thomann.xlsx"
    #
    # # Извлекаем данные из Excel
    # logger.info(f"Извлечение данных из {excel_file_path}...")
    # extracted_data = extract_column_a_from_excel(excel_file_path)
    #
    # # Сохраняем извлеченные данные в JSON
    # with open("extracted_urls.json", "w", encoding="utf-8") as f:
    #     json.dump(extracted_data, f, indent=4, ensure_ascii=False)
    # logger.info(f"Данные сохранены в extracted_urls.json")

    # Загружаем данные из JSON-файла
    json_file = "test_one_url.json"  # "extracted_urls.json" для всех URL
    with open(json_file, "r", encoding="utf-8") as f:
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
        "Использовать многопоточное скачивание пакетов? (y/n, по умолчанию y): "
    )
    use_threading = threading_mode.lower() != "n"

    # Скачиваем все страницы асинхронно
    download_all_pages_async(extracted_data, use_threading)


if __name__ == "__main__":
    main()
