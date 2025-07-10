# src/main_controller.py
import asyncio
import json
import math
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


async def get_products():

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

    # def get_after(page, items_per_page=20):
    #     """
    #     Возвращает значение 'after' для GraphQL-запроса на основе номера страницы.

    #     Args:
    #         page (int): Номер страницы (начинается с 1).
    #         items_per_page (int): Количество элементов на страницу (по умолчанию 20).

    #     Returns:
    #         str: Значение 'after' для указанной страницы или пустая строка для страницы 1.
    #     """
    #     if not isinstance(page, int) or page < 1:
    #         raise ValueError("Page must be a positive integer")

    #     if page == 1:
    #         return ""

    #     # Вычисляем индекс последнего элемента предыдущей страницы
    #     last_index = (page - 1) * items_per_page - 1
    #     # Формируем строку after в формате arrayconnection:<index>
    #     return f"YXJyYXljb25uZWN0aW9uO{last_index}"

    # async def get_first_page():
    #     """
    #     Получить первую страницу каталога и вычислить общее количество страниц

    #     Returns:
    #         int: Общее количество страниц или None при ошибке
    #     """
    #     json_page = get_path("json_page")

    #     # JSON данные для первой страницы
    #     json_data = {
    #         "operationName": "Store",
    #         "variables": {
    #             "currency": "UAH",
    #             "context": {
    #                 "country": "UA",
    #                 "region": "ukraine",
    #                 "language": "en",
    #             },
    #             "searchType": "DEFAULT",
    #             "types": [
    #                 "game",
    #             ],
    #             "drms": [
    #                 "xbox",
    #             ],
    #             "regions": [
    #                 "argentina",
    #                 "turkey",
    #                 "united_states",
    #                 "europe",
    #                 "global",
    #             ],
    #             "sortBy": "POPULARITY_DESC",
    #             "after": "",
    #             "first": 20,
    #             "price": {
    #                 "to": 100000,
    #                 "currency": "UAH",
    #             },
    #             "url": "/store/games",
    #             "redirectUrl": "https://www.eneba.com/store/games",
    #         },
    #         "extensions": {
    #             "persistedQuery": {
    #                 "version": 1,
    #                 "sha256Hash": "e7c4cb284593ba8790a73238ee99c8b3cceb6dae6a3bd6a3eb46de758bab688e_fa9d4ba78292d78e2783bcbfcafd66f124a700122195de5fb927b7244800cf5a3e299cb9abf45322afaac142ce79f9f89d4447d0d908f83f9ff19f79be55f40e",
    #             },
    #         },
    #     }

    #     # Имя файла для первой страницы
    #     first_page_filename = json_page / "eneba_page_1.json"

    #     try:
    #         # Выполняем POST запрос
    #         success = await downloader.post_url(
    #             url="https://www.eneba.com/graphql/",
    #             json_data=json_data,
    #             filename=first_page_filename,
    #         )

    #         if not success:
    #             logger.error("❌ Не удалось получить первую страницу")
    #             return None

    #         # Читаем сохраненный файл для анализа
    #         with open(first_page_filename, "r", encoding="utf-8") as f:
    #             response_data = json.load(f)

    #         # Извлекаем totalCount
    #         try:
    #             total_count = response_data["data"]["search"]["results"]["totalCount"]
    #             logger.info(f"📊 Найдено товаров: {total_count}")

    #             # Вычисляем количество страниц
    #             items_per_page = 20
    #             total_pages = math.ceil(total_count / items_per_page)

    #             logger.info(f"📄 Общее количество страниц: {total_pages}")
    #             return total_pages

    #         except (KeyError, TypeError) as e:
    #             logger.error(f"❌ Ошибка при извлечении totalCount: {e}")
    #             logger.debug(
    #                 f"Структура ответа: {list(response_data.keys()) if isinstance(response_data, dict) else 'не словарь'}"
    #             )
    #             return None

    #     except Exception as e:
    #         logger.error(f"❌ Ошибка при получении первой страницы: {e}")
    #         return None

    # async def get_all_pages():
    """
    Получить все страницы каталога на основе первой страницы

    Returns:
        bool: True если успешно, False при ошибке
    """
    # # Получаем информацию о первой странице
    # catalog_info = await get_first_page()

    # if not catalog_info:
    #     logger.error("❌ Не удалось получить информацию о каталоге")
    #     return False

    # total_pages = catalog_info["total_pages"]
    # logger.info(f"🚀 Начинаем загрузку {total_pages} страниц")

    # # Создаем задачи для остальных страниц
    # tasks = []
    # json_directory = get_path("json_dir")
    # category_id = get_path("category_id")

    # for page_num in range(2, total_pages + 1):  # Начинаем с 2-й страницы
    #     # Вычисляем offset для страницы
    #     offset = (page_num - 1) * 20
    #     after = get_after(page_num)
    #     json_data = {
    #         "operationName": "Store",
    #         "variables": {
    #             "currency": "UAH",
    #             "context": {
    #                 "country": "UA",
    #                 "region": "ukraine",
    #                 "language": "en",
    #             },
    #             "searchType": "DEFAULT",
    #             "types": [
    #                 "game",
    #             ],
    #             "drms": [
    #                 "xbox",
    #             ],
    #             "regions": [
    #                 "argentina",
    #                 "turkey",
    #                 "united_states",
    #                 "europe",
    #                 "global",
    #             ],
    #             "sortBy": "POPULARITY_DESC",
    #             "after": after,
    #             "first": 20,
    #             "price": {
    #                 "to": 100000,
    #                 "currency": "UAH",
    #             },
    #             "url": "/store/games",
    #             "redirectUrl": "https://www.eneba.com/store/games",
    #         },
    #         "extensions": {
    #             "persistedQuery": {
    #                 "version": 1,
    #                 "sha256Hash": "e7c4cb284593ba8790a73238ee99c8b3cceb6dae6a3bd6a3eb46de758bab688e_fa9d4ba78292d78e2783bcbfcafd66f124a700122195de5fb927b7244800cf5a3e299cb9abf45322afaac142ce79f9f89d4447d0d908f83f9ff19f79be55f40e",
    #             },
    #         },
    #     }

    #     page_filename = json_directory / f"eneba_page_{page_num}.json"

    #     task = downloader.post_url(
    #         url="https://www.eneba.com/graphql/",
    #         json_data=json_data,
    #         filename=page_filename,
    #     )

    #     tasks.append((page_num, task))

    # # Выполняем все задачи параллельно
    # if tasks:
    #     logger.info(f"📥 Загружаем {len(tasks)} страниц параллельно...")

    #     completed_tasks = await asyncio.gather(
    #         *[task for _, task in tasks], return_exceptions=True
    #     )

    #     # Анализируем результаты
    #     successful = 0
    #     for (page_num, _), result in zip(tasks, completed_tasks):
    #         if isinstance(result, Exception):
    #             logger.error(f"❌ Ошибка на странице {page_num}: {result}")
    #         elif result:
    #             successful += 1
    #             logger.debug(f"✅ Страница {page_num} загружена")
    #         else:
    #             logger.warning(f"⚠️ Страница {page_num} не загружена")

    #     logger.info(
    #         f"📊 Загружено страниц: {successful + 1}/{total_pages} (включая первую)"
    #     )
    #     return successful > 0

    # else:
    #     logger.info("📄 Только одна страница в каталоге")
    #     return True


# Оставим закрытой
# async def get_products():
#     logger.info("Запуск процесса получения данных о товарах через Playwright")
#     html_product = get_path("html_product")
#     category_id = get_path("category_id")
#     # Получаем данные продуктов из БД для выбранной категории
#     skugs = get_product_data(category_id=category_id)

#     if not skugs:
#         logger.error(f"Нет данных для обработки в категории {category_id}")
#         return False

#     results = await downloader.download_urls(skugs)

#     # Анализируем результаты
#     successful = sum(1 for success in results.values() if success)
#     logger.info(f"✅ Успешно обработано: {successful}/{len(skugs)} товаров")

#     failed_slugs = [slug for slug, success in results.items() if not success]
#     if failed_slugs:
#         logger.warning(f"❌ Неудачные запросы для: {failed_slugs}")

#     return results


async def get_products_img_rozetka():
    category_id = get_rozetka_path("category_id")
    # Получаем данные продуктов из БД для выбранной категории

    skugs = get_product_data_rozetka(category_id=category_id)

    if not skugs:
        logger.error(f"Нет данных для обработки в категории {category_id}")
        return False
    await downloader.download_urls(skugs)


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
    print("3. Обработать страницы с товаром")
    print("4. Скачать файлы для обновления цен на товары")
    print("5. Скачать файлы для обновления ссылок на изображения")
    print("6. Обновить данны из пункта 4 и 5")
    print("7. Только обновить цены согласно config")
    print("8. Загрузить уникальные ID товаров из Excel")
    print("9. Очистить временные файлы для категории")
    print("0. Выход")
    print("=" * 50)


def main():
    while True:
        display_menu()
        choice = input("Выберите действие (0-9): ").strip()

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
                # asyncio.run(get_first_page())
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
                asyncio.run(get_products())

        elif choice == "5":
            if marketpalses == "1":
                asyncio.run(get_products_img_rozetka())
            else:
                asyncio.run(get_products_img_rozetka())

        elif choice == "6":
            if marketpalses == "1":
                category_id = get_path("category_id")
                all_data, bd_json_path = parse_json_and_html_files(category_id)
                if all_data:
                    updated_prices, updated_images, errors = update_prices_and_images(
                        bd_json_path, category_id=category_id
                    )
                    export_data_to_excel(category_id=category_id)
                else:
                    logger.error("Нет данных для обновления")
            else:
                category_id = get_rozetka_path("category_id")
                logger.info(f"Обрабатываем данные для категории Rozetka: {category_id}")

                all_data, bd_json_path = parse_json_and_html_files_rozetka(category_id)
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

        # elif choice == "9":
        #     if marketpalses == "1":
        #         clean_temp_files()
        #     else:
        #         # ИСПРАВЛЕНИЕ: Добавляем очистку файлов для Rozetka
        #         clean_rozetka_temp_files()

        else:
            logger.error("Некорректный выбор операции")

        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()
