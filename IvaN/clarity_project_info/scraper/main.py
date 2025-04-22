import asyncio

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
from utils.csv_utils import extract_and_save_specific_urls, load_urls, write_csv
from utils.download_utils import (
    async_download_html_with_proxies,
    download_file,
    download_gz_files,
)
from utils.file_utils import create_directories, extract_gz_files
from utils.proxy_utils import load_proxies
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
        # # Шаг 1: Скачать основной файл sitemap-index.xml
        # logger.info("Шаг 1: Скачивание основного файла sitemap")
        # download_file(SITEMAP_INDEX_URL, XML_SITEMAP, proxies)

        # # Шаг 2: Парсинг и запись ссылок в CSV
        # logger.info("Шаг 2: Парсинг sitemap-index")
        # sitemap_links = parse_sitemap_index(XML_SITEMAP)
        # write_csv(CSV_URL_SITE_MAPS, sitemap_links)

        # # Шаг 3: Скачивание .xml.gz файлов
        # logger.info(f"Шаг 3: Скачивание {len(sitemap_links)} архивов")
        # download_gz_files(sitemap_links, GZ_DIR, proxies, MAX_WORKERS)

        # # Шаг 4: Распаковка .gz файлов
        # logger.info("Шаг 4: Распаковка архивов")
        # extract_gz_files(GZ_DIR, XML_DIR)

        # # Шаг 5: Парсинг URL продуктов из XML файлов
        # logger.info("Шаг 5: Парсинг XML файлов")
        # process_xml_files(XML_DIR, CSV_ALL_URLS_PRODUCTS)

        # # Шаг 6: Фильтрация URL по подстроке
        # logger.info(f"Шаг 6: Фильтрация URL по подстроке '{substring}'")
        # extract_and_save_specific_urls(
        #     CSV_ALL_URLS_PRODUCTS, CSV_ALL_EDRS_PRODUCTS, substring
        # )

        # Шаг 7: Скачивание HTML страниц
        logger.info("Шаг 7: Скачивание HTML страниц")
        urls = load_urls(CSV_ALL_EDRS_PRODUCTS)
        asyncio.run(
            async_download_html_with_proxies(urls, proxies, HTML_FILES_DIR, MAX_WORKERS)
        )

        logger.info("Работа завершена успешно!")

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


if __name__ == "__main__":
    main()
