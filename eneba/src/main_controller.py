# src/main_controller.py
import asyncio
import shutil
from pathlib import Path

from config_utils import load_config
from logger import logger
from main_bd import get_product_data, update_prices_and_images
from main_page import (
    download_pages,
    extract_ids_from_excel,
    process_html_files,
    update_prices_from_config,
)
from main_pl import run as run_playwright
from main_product import export_data_to_excel, parse_json_and_html_files
from path_manager import get_path, is_initialized, select_category_and_init_paths
from playwright.async_api import async_playwright

config = load_config()
BASE_DIR = Path(__file__).parent.parent
cookies = config["cookies"]
headers = config["headers"]


def display_menu():
    """Отображает основное меню"""
    print("\n" + "=" * 50)
    print("ENEBA - УПРАВЛЕНИЕ КАТЕГОРИЯМИ ТОВАРОВ")
    print("=" * 50)
    print("1. Полный цикл (скачать HTML -> обработать товары -> обновить цены)")
    print("2. Только скачать HTML-страницы")
    print("3. Только обработать существующие HTML-страницы")
    print("4. Только загрузить данные о товарах из API")
    print("5. Только обработать JSON и HTML файлы товаров")
    print("6. Только обновить цены")
    print("7. Загрузить уникальные ID товаров из Excel")
    print("8. Очистить временные файлы для категории")
    print("0. Выход")
    print("=" * 50)


async def run_playwright_process():
    """Запускает процесс загрузки данных с помощью Playwright"""
    logger.info("Запуск процесса получения данных о товарах через Playwright")

    category_id = get_path("category_id")
    # Получаем данные продуктов из БД для выбранной категории
    skugs = get_product_data(category_id=category_id)

    if not skugs:
        logger.error(f"Нет данных для обработки в категории {category_id}")
        return False

    logger.info(f"Найдено {len(skugs)} товаров для обработки в категории {category_id}")

    # Запускаем обработку
    async with async_playwright() as playwright:
        await run_playwright(playwright, skugs)

    return True


def run_full_cycle():
    """Выполняет полный цикл обработки для категории"""
    url = get_path("url")
    start_page = get_path("start_page")
    num_pages = get_path("num_pages")
    delay = get_path("delay")
    category_name = get_path("category_name")
    category_id = get_path("category_id")
    logger.info(
        f"Запуск полного цикла обработки для категории: {category_name} (ID: {category_id})"
    )

    # 1. Скачиваем страницы

    logger.info(f"Шаг 1: Скачивание HTML-страниц с {url}")
    download_pages(url, start_page, num_pages, cookies, headers, delay)

    # 2. Обрабатываем HTML и создаем JSON для базы данных
    logger.info("Шаг 2: Обработка HTML-страниц и создание JSON для базы данных")
    all_products = process_html_files()

    if not all_products or len(all_products) == 0:
        logger.error("Не удалось получить данные товаров из HTML")
        return False

    # 3. Получаем данные о товарах через Playwright
    logger.info("Шаг 3: Получение данных о товарах через Playwright")
    asyncio.run(run_playwright_process())

    # 4. Обрабатываем JSON и HTML файлы товаров
    logger.info("Шаг 4: Обработка JSON и HTML файлов товаров")
    all_data, bd_json_path = parse_json_and_html_files()

    # 5. Обновляем данные в БД
    logger.info("Шаг 5: Обновление цен и изображений в базе данных")
    updated_prices, updated_images, errors = update_prices_and_images(
        bd_json_path, category_id=category_id
    )

    logger.info(
        f"Обновление данных в БД: цены - {updated_prices}, изображения - {updated_images}, ошибки - {errors}"
    )

    # 6. Экспортируем в Excel
    logger.info("Шаг 6: Экспорт данных в Excel")
    export_data_to_excel(category_id=category_id)

    # 7. Обновляем цены по настроенным правилам
    logger.info("Шаг 7: Обновление цен по настроенным правилам")
    update_prices_from_config()

    logger.info("Полный цикл обработки завершен!")
    return True


def clean_temp_files():
    """Очищает временные файлы для выбранной категории"""
    html_page = get_path("html_page")
    html_product = get_path("html_product")
    json_dir = get_path("json_dir")
    category_name = get_path("category_name")
    if html_page.exists():
        logger.info(f"Удаление HTML-страниц для категории {category_name}")
        shutil.rmtree(html_page)
        html_page.mkdir(parents=True, exist_ok=True)

    if html_product.exists():
        logger.info(f"Удаление HTML-товаров для категории {category_name}")
        shutil.rmtree(html_product)
        html_product.mkdir(parents=True, exist_ok=True)

    if json_dir.exists():
        logger.info(f"Удаление JSON-файлов для категории {category_name}")
        shutil.rmtree(json_dir)
        json_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Временные файлы для категории {category_name} успешно очищены")


def main():
    from main_bd import get_product_data, update_prices_and_images
    from main_page import (
        download_pages,
        extract_ids_from_excel,
        process_html_files,
        update_prices_from_config,
    )
    from main_pl import run as run_playwright
    from main_product import export_data_to_excel, parse_json_and_html_files

    while True:
        display_menu()
        choice = input("Выберите действие (0-8): ").strip()

        if choice == "0":
            logger.info("Выход из программы")
            break

        # Для всех пунктов, кроме выхода, нужно выбрать категорию
        if (
            not is_initialized() or choice == "9"
        ):  # Добавляем скрытую опцию для смены категории
            category_info = select_category_and_init_paths()
            if not category_info:
                print("Для продолжения работы необходимо выбрать категорию")
                continue

        if choice == "1":
            # Полный цикл
            run_full_cycle()

        elif choice == "2":
            # Только скачать HTML-страницы

            download_pages()

        elif choice == "3":
            # Только обработать существующие HTML-страницы
            process_html_files()

        elif choice == "4":
            # Только загрузить данные о товарах из API
            asyncio.run(run_playwright_process())

        elif choice == "5":
            # Только обработать JSON и HTML файлы товаров
            all_data, bd_json_path = parse_json_and_html_files()
            if all_data:

                updated_prices, updated_images, errors = update_prices_and_images(
                    bd_json_path, category_id=category_id
                )
                export_data_to_excel(category_id=category_id)
            else:
                logger.error("Нет данных для обновления")

        elif choice == "6":
            # Только обновить цены
            update_prices_from_config()

        elif choice == "7":
            # Загрузить уникальные ID товаров из Excel
            extract_ids_from_excel()

        elif choice == "8":
            # Очистить временные файлы
            clean_temp_files()

        else:
            logger.error("Некорректный выбор операции")

        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()
