from loguru import logger
from pathlib import Path
from dotenv import dotenv_values
from configuration.configurat import LOG_PATH

# Используем путь из config.py
log_directory = Path(LOG_PATH)

# Создание директории логов, если её нет
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

log_file_path = Path(log_directory, "log_message.log")
logger.add(
    log_file_path,
    format="{time:DD-MM-YYYY HH:mm:ss} - {level} - {name}:{line} - {message}",
    level="DEBUG",
    encoding="utf-8",
)
