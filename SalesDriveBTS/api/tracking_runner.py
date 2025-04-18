# api/tracking_runner.py
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent))

from services.tracking_service import start_tracking_service
from core.logger import logger

if __name__ == "__main__":
    try:
        logger.info("Запуск службы отслеживания статусов заказов")
        # Запускаем сервис отслеживания
        start_tracking_service()
    except KeyboardInterrupt:
        logger.info("Служба отслеживания остановлена пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка в службе отслеживания: {e}")
        sys.exit(1)