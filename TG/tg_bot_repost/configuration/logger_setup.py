import sys
from pathlib import Path

from loguru import logger

current_directory = Path.cwd()
logging_directory = current_directory / "logging"
logging_directory.mkdir(parents=True, exist_ok=True)

log_file_path = logging_directory / "log_message.log"

# Логирование в файл с ротацией и удалением старых логов
logger.add(
    log_file_path,
    format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {name} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
)

# # Логирование в консоль
# logger.add(
#     sys.stdout,
#     format="{time:DD-MM-YYYY HH:mm:ss} - {level} - {name}:{line} - {message}",
#     level="DEBUG",
# )
