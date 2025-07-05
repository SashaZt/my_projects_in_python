# src/main_controller.py
import asyncio
import shutil
import time
from pathlib import Path

from config_utils import load_config
from downloader import downloader
from logger import logger
from main_bd import (
    get_product_data,
    get_product_data_rozetka,
    update_prices_and_images,
    update_rozetka_prices_and_images,
)
from main_page import (
    download_pages,
    extract_ids_from_excel,
    process_html_files,
    update_prices_from_config,
    update_prices_from_config_rozetka,
)
from main_pl import run as run_playwright
from main_product import (
    export_data_to_excel,
    export_data_to_excel_rozetka,
    parse_json_and_html_files,
    parse_json_and_html_files_rozetka,
)
from path_manager import get_path, is_initialized, select_category_and_init_paths
from playwright.async_api import async_playwright
from rozetka_page import process_rozetka_html_files
from rozetka_path_manager import (
    get_rozetka_path,
    select_rozetka_category_and_init_paths,
)

config = load_config()
BASE_DIR = Path(__file__).parent.parent
cookies = config["cookies"]
headers = config["headers"]


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


async def get_pages():
    logger.info("Запуск процесса получения данных о товарах через Playwright")

    category_id = get_path("category_id")
    # Получаем данные продуктов из БД для выбранной категории
    skugs = get_product_data(category_id=category_id)

    if not skugs:
        logger.error(f"Нет данных для обработки в категории {category_id}")
        return False

    # JSON template для GraphQL запроса (НЕ form_template!)
    json_template = {
        "operationName": "WickedNoCache",
        "variables": {
            "isAutoRenewActive": False,
            "isProductVariantSearch": False,
            "isCheapestAuctionIncluded": True,
            "currency": "UAH",
            "context": {
                "country": "UA",
                "region": "ukraine",
                "language": "en",
            },
            "slug": "{slug}",  # Здесь будет подставляться каждый slug
            "language": "en",
            "utmValues": {
                "enbCampaign": "Homepage",
                "enbContent": "Main%20Categories%20Navigation",
                "enbMedium": "link",
                "enbSource": "https%3A%2F%2Fwww.eneba.com%2F",
                "enbTerm": "Games",
            },
            "version": 7,
            "abTests": [
                "CFD755",
            ],
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "87a1e783618b16092767beb84810a3a1a2adcba553d18620e59bf993da0b34f2_1daa7330a8898875b69f4c9119b0bc8f66ef99e8c08106610e49d36c4304c83c723c8d06383387f17ee1fc326ea96f8c95ad2a91d3be11ae5983eb1acf150b05",
            },
        },
    }

    # Создаем кастомные имена файлов для каждого slug
    # custom_filenames = {slug: Path(f"json/{category_id}/{slug}.json") for slug in skugs}

    # Используем json_template, а не data_template для GraphQL
    results = await downloader.post_skus(
        base_url="https://www.eneba.com/graphql/",
        skugs=skugs,
        json_template=json_template,  # Исправлено: используем json_template
    )

    # Анализируем результаты
    successful = sum(1 for success in results.values() if success)
    logger.info(f"✅ Успешно обработано: {successful}/{len(skugs)} товаров")

    failed_slugs = [slug for slug, success in results.items() if not success]
    if failed_slugs:
        logger.warning(f"❌ Неудачные запросы для: {failed_slugs}")

    return results


async def get_products():
    logger.info("Запуск процесса получения данных о товарах через Playwright")
    html_product = get_path("html_product")
    category_id = get_path("category_id")
    # Получаем данные продуктов из БД для выбранной категории
    skugs = get_product_data(category_id=category_id)

    if not skugs:
        logger.error(f"Нет данных для обработки в категории {category_id}")
        return False

    results = await downloader.download_urls(skugs)

    # Анализируем результаты
    successful = sum(1 for success in results.values() if success)
    logger.info(f"✅ Успешно обработано: {successful}/{len(skugs)} товаров")

    failed_slugs = [slug for slug, success in results.items() if not success]
    if failed_slugs:
        logger.warning(f"❌ Неудачные запросы для: {failed_slugs}")

    return results


async def get_products_rozetka():
    category_id = get_rozetka_path("category_id")
    # Получаем данные продуктов из БД для выбранной категории
    skugs = get_product_data_rozetka(category_id=category_id)

    if not skugs:
        logger.error(f"Нет данных для обработки в категории {category_id}")
        return False

    await downloader.download_urls(skugs)

    # # Анализируем результаты
    # successful = sum(1 for success in results.values() if success)
    # logger.info(f"✅ Успешно обработано: {successful}/{len(skugs)} товаров")

    # failed_slugs = [slug for slug, success in results.items() if not success]
    # if failed_slugs:
    #     logger.warning(f"❌ Неудачные запросы для: {failed_slugs}")

    # return results


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


def display_menu():
    """Отображает основное меню"""
    print("\n" + "=" * 50)
    print("ENEBA - УПРАВЛЕНИЕ КАТЕГОРИЯМИ ТОВАРОВ")
    print("=" * 50)
    print("1. Полный цикл (скачать HTML -> обработать товары -> обновить цены)")
    print("2. Только скачать HTML-страницы")
    print("3. Только обработать существующие HTML-страницы")
    print("4. Обновить цены о товарах")
    print("5. Обновить ссылки на товары")
    print("6. Только обработать JSON и HTML файлы товаров")
    print("7. Только обновить цены")
    print("8. Загрузить уникальные ID товаров из Excel")
    print("9. Очистить временные файлы для категории")
    print("0. Выход")
    print("=" * 50)


def main():
    while True:
        display_menu()
        choice = input("Выберите действие (0-8): ").strip()

        if choice == "0":
            logger.info("Выход из программы")
            break

        if choice in {"2", "3", "4", "5", "6", "7"}:
            marketpalses = input("Выберите Пром - 1, Розетка - 2: ").strip()
            if marketpalses == "1":
                if not is_initialized():
                    category_info = select_category_and_init_paths()
                    if not category_info:
                        print("Для продолжения работы необходимо выбрать категорию")
                        continue
            else:
                category_info = select_rozetka_category_and_init_paths()
                if not category_info:
                    print("Для продолжения работы необходимо выбрать категорию Rozetka")
                    continue

        if choice == "1":
            logger.info("ТУТ ничего нету ;)")

        elif choice == "2":
            if marketpalses == "1":
                url = get_path("url")
                download_pages(url, cookies, headers)
            else:
                # Для Rozetka тоже нужна функция скачивания страниц
                logger.info("Функция скачивания страниц для Rozetka в разработке")

        elif choice == "3":
            if marketpalses == "1":
                process_html_files()
            else:
                process_rozetka_html_files()

        elif choice == "4":
            if marketpalses == "1":
                # asyncio.run(run_playwright_process())
                asyncio.run(get_pages())

            else:
                asyncio.run(get_products())
        elif choice == "5":
            if marketpalses == "1":
                asyncio.run(get_products())
            else:
                asyncio.run(get_products_rozetka())

        elif choice == "6":
            if marketpalses == "1":
                all_data, bd_json_path = parse_json_and_html_files()
                if all_data:
                    category_id = get_path("category_id")
                    updated_prices, updated_images, errors = update_prices_and_images(
                        bd_json_path, category_id=category_id
                    )
                    export_data_to_excel(category_id=category_id)
                else:
                    logger.error("Нет данных для обновления")
            else:
                category_id = get_rozetka_path("category_id")
                logger.info(f"Обрабатываем данные для категории Rozetka: {category_id}")

                all_data, bd_json_path = parse_json_and_html_files_rozetka()
                if all_data:
                    updated_prices, updated_images, errors = (
                        update_rozetka_prices_and_images(
                            bd_json_path, category_id=category_id
                        )
                    )
                    # ИСПРАВЛЕНИЕ: Передаем category_id в функцию экспорта
                    export_data_to_excel_rozetka(category_id=category_id)
                else:
                    logger.error("Нет данных для обновления Rozetka")

        elif choice == "7":
            if marketpalses == "1":
                update_prices_from_config()
            else:
                update_prices_from_config_rozetka()

        elif choice == "8":
            extract_ids_from_excel()

        elif choice == "9":
            if marketpalses == "1":
                clean_temp_files()
            else:
                # ИСПРАВЛЕНИЕ: Добавляем очистку файлов для Rozetka
                clean_rozetka_temp_files()

        else:
            logger.error("Некорректный выбор операции")

        input("\nНажмите Enter для продолжения...")


def clean_rozetka_temp_files():
    """Очищает временные файлы для выбранной категории Rozetka"""

    html_page = get_rozetka_path("html_page")
    html_product = get_rozetka_path("html_product")
    json_dir = get_rozetka_path("json_dir")
    category_name = get_rozetka_path("category_name")

    if html_page and html_page.exists():
        logger.info(f"Удаление HTML-страниц Rozetka для категории {category_name}")
        shutil.rmtree(html_page)
        html_page.mkdir(parents=True, exist_ok=True)

    if html_product and html_product.exists():
        logger.info(f"Удаление HTML-товаров Rozetka для категории {category_name}")
        shutil.rmtree(html_product)
        html_product.mkdir(parents=True, exist_ok=True)

    if json_dir and json_dir.exists():
        logger.info(f"Удаление JSON-файлов Rozetka для категории {category_name}")
        shutil.rmtree(json_dir)
        json_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Временные файлы Rozetka для категории {category_name} успешно очищены"
    )


if __name__ == "__main__":
    main()
