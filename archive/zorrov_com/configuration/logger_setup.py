from pathlib import Path
from loguru import logger

# Получаем текущую директорию
current_directory = Path.cwd()

# Определяем директорию для логов
logging_directory = "logging"
logging_path = current_directory / logging_directory

# Создание директории для логов, если она не существует
logging_path.mkdir(parents=True, exist_ok=True)

# Путь к файлу логов
log_file_path = logging_path / "log_message.log"

# Настройка логирования
logger.add(
    log_file_path,
    format="{time:DD-MM-YYYY HH:mm:ss} - {level} - {message}",
    level="DEBUG",
    encoding="utf-8",
)
