from loguru import logger
import os

current_directory = os.getcwd()
logging_path = os.path.join(current_directory, "logging")
current_directory = os.getcwd()


# Настройки loguru
filename = os.path.join(logging_path, "log.log")
logger.remove()
logger.add(filename, rotation="10 MB", compression="zip", level="INFO")
# Пример использования
logger.info("Настройка логирования завершена.")
