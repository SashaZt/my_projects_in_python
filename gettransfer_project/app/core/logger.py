import sys
from loguru import logger
from pathlib import Path

# Определяем текущую директорию (где находится этот файл) и создаем папку log
current_directory = Path(__file__).parent.resolve()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"

# Удаляем стандартную конфигурацию логгера
logger.remove()

# Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)
