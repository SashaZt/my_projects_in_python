import asyncio
from pathlib import Path
from urllib.parse import urlparse

from config.constants import (
    CONFIG_DIR,
    CSV_ALL_EDRS_PRODUCTS,
    CSV_ALL_URLS_PRODUCTS,
    CSV_URL_SITE_MAPS,
    DATA_DIR,
    FILE_PROXY,
    GZ_DIR,
    HTML_FILES_DIR,
    XML_DIR,
    XML_SITEMAP,
)
from config.logger import logger
from utils.creative_list_urls import generate_edr_urls_to_csv
from utils.csv_utils import extract_and_save_specific_urls, load_urls, write_csv
from utils.download_utils import (
    async_download_html_with_proxies,
    download_file,
    download_gz_files,
)
from utils.file_utils import create_directories, extract_gz_files
from utils.main_edrpo import import_json_to_postgres
from utils.main_financi import import_finance_json_to_postgres
from utils.proxy_utils import load_proxies
from utils.scrap_utils import parse_all_files_and_save_to_excel
from utils.xml_utils import parse_sitemap_index, process_xml_files

from config.config import MAX_WORKERS, PROXY_ENABLED, SITEMAP_INDEX_URL


def main():
    """Главная функция приложения."""
    # Создаем необходимые директории
    create_directories(GZ_DIR, XML_DIR, HTML_FILES_DIR, DATA_DIR, CONFIG_DIR)

    # Загружаем прокси, если включены
    proxies = load_proxies(FILE_PROXY) if PROXY_ENABLED else []
    logger.info(
        f"Загружено прокси: {len(proxies)}, прокси {'включены' if PROXY_ENABLED else 'отключены'}"
    )

    substring = "https://clarity-project.info/edr/"

    try:
        # Шаг 1: Скачать основной файл sitemap-index.xml
        logger.info("Шаг 1: Скачивание основного файла sitemap")
        download_file(SITEMAP_INDEX_URL, XML_SITEMAP, proxies)

        # Шаг 2: Парсинг и запись ссылок в CSV
        logger.info("Шаг 2: Парсинг sitemap-index")
        sitemap_links = parse_sitemap_index(XML_SITEMAP)
        write_csv(CSV_URL_SITE_MAPS, sitemap_links)

        # Шаг 3: Скачивание .xml.gz файлов
        logger.info("Шаг 3: Скачивание архивов")
        sitemap_links = load_urls(CSV_URL_SITE_MAPS)
        download_gz_files(sitemap_links, GZ_DIR, proxies, MAX_WORKERS)

        # Шаг 4: Распаковка .gz файлов
        logger.info("Шаг 4: Распаковка архивов")
        extract_gz_files(GZ_DIR, XML_DIR)

        # Шаг 5: Парсинг URL продуктов из XML файлов
        logger.info("Шаг 5: Парсинг XML файлов")
        process_xml_files(XML_DIR, CSV_ALL_URLS_PRODUCTS)

        # Шаг 6: Фильтрация URL по подстроке
        logger.info(f"Шаг 6: Фильтрация URL по подстроке '{substring}'")
        extract_and_save_specific_urls(
            CSV_ALL_URLS_PRODUCTS, CSV_ALL_EDRS_PRODUCTS, substring
        )

        # Шаг 7: Скачивание HTML страниц
        logger.info("Шаг 7: Скачивание HTML страниц")

        # Предварительная фильтрация URL - проверяем, какие HTML файлы уже существуют
        logger.info("Выполняем предварительную фильтрацию URL...")
        all_urls = load_urls(CSV_ALL_EDRS_PRODUCTS)

        # Фильтруем URL, для которых ещё нет HTML файлов

        missing_urls = []
        total_urls = len(all_urls)
        existing_count = 0

        logger.info(f"Проверка существующих файлов для {total_urls} URL...")

        for i, url in enumerate(all_urls):
            if i > 0 and i % 1000 == 0:
                logger.info(f"Проверено {i}/{total_urls} URL...")

            filename = HTML_FILES_DIR / f"{urlparse(url).path.replace('/', '_')}.html"
            if filename.exists():
                existing_count += 1
            else:
                missing_urls.append(url)

        logger.info(f"Найдено {existing_count} уже скачанных HTML файлов")
        logger.info(f"Осталось скачать {len(missing_urls)} HTML файлов")

        if not missing_urls:
            logger.info("Все файлы уже скачаны. Процесс завершен.")
        else:
            asyncio.run(
                async_download_html_with_proxies(
                    missing_urls, proxies, HTML_FILES_DIR, MAX_WORKERS
                )
            )

        logger.info("Работа завершена успешно!")

        # Парсинг данных
        max_threads = 100
        parse_all_files_and_save_to_excel(max_threads)

        # # 8 Импорт в БД которая в контейнер
        # import_json_to_postgres()
        # import_finance_json_to_postgres()

        # # Создание из файлов htmlсписка url для следующего парсинга
        # generate_edr_urls_to_csv()
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


if __name__ == "__main__":
    # while True:
    main()
