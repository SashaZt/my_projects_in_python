import asyncio
import sys

from config.logger import logger
from scrapers.excel_scraper import ExcelSheetScraper


def main():
    """Основная функция для запуска скрапера без аргументов"""
    logger.info("Запуск скрапера в непрерывном режиме без аргументов")

    # Инициализируем скрапер с дефолтными параметрами
    scraper = ExcelSheetScraper()

    try:
        # Запускаем основную функцию скрапера
        asyncio.run(scraper.main())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
