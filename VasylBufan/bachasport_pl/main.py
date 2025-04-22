import os
import sys
import time
from pathlib import Path
import argparse
from typing import Dict, List, Optional

from config.logger import logger
from src.auth import get_session
from src.category import get_category_urls
from src.pagination import get_product_urls_from_category
from src.product import get_product_details
from src.utils import random_pause
from src.xml_handler import (
    process_all_xml_files,
    save_products_to_csv,
    save_products_to_json,
)


def main():
    """
    Основная функция для запуска скрапинга.
    """
    parser = argparse.ArgumentParser(
        description="Скрапер для сайта panel.bachasport.pl"
    )
    parser.add_argument(
        "--max-categories",
        type=int,
        default=None,
        help="Максимальное количество категорий для обработки",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Максимальное количество страниц пагинации для обработки",
    )
    parser.add_argument(
        "--max-products",
        type=int,
        default=None,
        help="Максимальное количество продуктов для обработки",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Пропустить скачивание XML и обработать только существующие файлы",
    )
    args = parser.parse_args()

    start_time = time.time()
    logger.info("Запуск скрапера...")

    try:
        # Если указан флаг --skip-download, пропускаем скачивание и обрабатываем существующие XML
        if args.skip_download:
            logger.info("Режим обработки существующих XML файлов")
            products = process_all_xml_files()
            save_products_to_csv(products)
            save_products_to_json(products)
            elapsed_time = time.time() - start_time
            logger.info(
                f"Обработка завершена за {elapsed_time:.2f} секунд. Обработано {len(products)} продуктов."
            )
            return

        # Получаем авторизованную сессию
        session = get_session()
        if not session:
            logger.critical("Не удалось получить сессию. Завершение программы.")
            return

        # Получаем ссылки категорий со стартовой страницы
        category_urls = get_category_urls(session)
        if not category_urls:
            logger.error("Не удалось получить ссылки категорий. Завершение программы.")
            return

        logger.info(f"Найдено {len(category_urls)} категорий")

        # Ограничиваем количество категорий, если указано
        if args.max_categories and args.max_categories < len(category_urls):
            logger.info(
                f"Ограничение: обработка только {args.max_categories} из {len(category_urls)} категорий"
            )
            category_urls = category_urls[: args.max_categories]

        # Собираем URL продуктов из всех категорий
        all_product_urls = []
        for i, category_url in enumerate(category_urls):
            logger.info(
                f"Обработка категории {i+1}/{len(category_urls)}: {category_url}"
            )

            # Получаем URL продуктов из категории, включая пагинацию
            product_urls = get_product_urls_from_category(
                session, category_url, args.max_pages
            )
            all_product_urls.extend(product_urls)

            # Делаем паузу между обработкой разных категорий
            if i < len(category_urls) - 1:  # Не делаем паузу после последней категории
                random_pause(3, 8)

        # Удаляем дубликаты URL продуктов
        unique_product_urls = list(set(all_product_urls))
        logger.info(f"Найдено {len(unique_product_urls)} уникальных продуктов")

        # Ограничиваем количество продуктов, если указано
        if args.max_products and args.max_products < len(unique_product_urls):
            logger.info(
                f"Ограничение: обработка только {args.max_products} из {len(unique_product_urls)} продуктов"
            )
            unique_product_urls = unique_product_urls[: args.max_products]

        # Скачиваем XML каждого продукта
        success_count = 0
        for i, product_url in enumerate(unique_product_urls):
            logger.info(
                f"Обработка продукта {i+1}/{len(unique_product_urls)}: {product_url}"
            )

            # Получаем детали продукта и скачиваем XML
            product_id, xml_path = get_product_details(session, product_url)

            if product_id and xml_path:
                success_count += 1
                logger.info(f"Успешно скачан XML для продукта {product_id}")
            else:
                logger.warning(f"Не удалось скачать XML для продукта {product_url}")

            # Делаем паузу между запросами к продуктам
            if (
                i < len(unique_product_urls) - 1
            ):  # Не делаем паузу после последнего продукта
                random_pause(1, 4)

        logger.info(
            f"Скачивание XML завершено. Успешно: {success_count}/{len(unique_product_urls)}"
        )

        # Обрабатываем скачанные XML и сохраняем результаты
        products = process_all_xml_files()
        save_products_to_csv(products)
        save_products_to_json(products)

        elapsed_time = time.time() - start_time
        logger.info(
            f"Скрапинг успешно завершен за {elapsed_time:.2f} секунд. Обработано {len(products)} продуктов."
        )

    except KeyboardInterrupt:
        logger.info("Скрапинг прерван пользователем.")
    except Exception as e:
        logger.critical(f"Критическая ошибка в основной функции: {e}")


if __name__ == "__main__":
    main()
