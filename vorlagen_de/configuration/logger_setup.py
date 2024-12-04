import os

from loguru import logger

# Создаем директорию для логов
current_directory = os.getcwd()
logging_directory = "logging"
logging_path = os.path.join(current_directory, logging_directory)
os.makedirs(logging_path, exist_ok=True)

# Путь к файлу логов
log_file_path = os.path.join(logging_path, "log_message.log")

# Настраиваем логгер с ротацией при достижении размера 1 Мб
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {name}:{line} - {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="1 MB",  # Ротация при достижении 1 Мб
    compression=None,  # Опционально: не сжимать старые файлы
)
