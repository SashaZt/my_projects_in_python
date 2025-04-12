import argparse
import asyncio
import os
import sys
from pathlib import Path

from kostrost.all_site.config.logger import logger
from scraper import ExcelSheetScraper


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(description="Скрапер URL из Excel по листам")

    parser.add_argument(
        "--excel", type=str, default="thomann.xlsx", help="Путь к Excel файлу с URL"
    )

    parser.add_argument(
        "--html-dir",
        type=str,
        default="html_pages",
        help="Директория для сохранения HTML файлов",
    )

    parser.add_argument(
        "--jobs-dir",
        type=str,
        default="json_jobs",
        help="Директория для хранения информации о заданиях",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default="d415ddc01cf23948eff76e4447f69372",
        help="API ключ для ScraperAPI",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Тестовый режим (по одному URL с каждого листа)",
    )

    return parser.parse_args()


async def main():
    """Основная функция для запуска скрапера"""
    args = parse_arguments()

    # Проверяем существование Excel файла
    excel_path = Path(args.excel)
    if not excel_path.exists():
        logger.error(f"Excel файл не найден: {args.excel}")
        sys.exit(1)

    # Инициализируем скрапер
    scraper = ExcelSheetScraper(
        api_key=args.api_key,
        excel_file_path=args.excel,
        base_html_dir=args.html_dir,
        json_dir=args.jobs_dir,
    )

    if args.test:
        logger.info("Запуск в тестовом режиме (по одному URL с каждого листа)")
        # Извлекаем URL из Excel
        sheet_urls = scraper.extract_urls_from_excel()

        # Оставляем только по одному URL с каждого листа
        test_sheet_urls = {
            sheet: [urls[0]] for sheet, urls in sheet_urls.items() if urls
        }

        # Отправляем задания
        if scraper.submit_jobs(test_sheet_urls):
            logger.info("Тестовые задания отправлены, получаем результаты")
            await scraper.fetch_results_async()
        else:
            logger.warning("Нет URL для обработки или все файлы уже существуют")
    else:
        # Запускаем обычный режим
        logger.info("Запуск в обычном режиме (все URL)")
        await scraper.main()

    logger.info("Скрапинг завершен")


if __name__ == "__main__":
    try:
        # Запуск асинхронной функции
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        sys.exit(1)
