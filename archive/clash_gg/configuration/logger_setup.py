import sys
from loguru import logger

# Отключаем стандартный обработчик
logger.remove()

# Логирование в консоль
logger.add(
    sys.stdout,
    format="{time:DD-MM-YYYY HH:mm:ss} - {level} - {message}",
    level="DEBUG",
)
