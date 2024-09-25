from loguru import logger
import sys

logger.add(
    sys.stdout,
    format="{time:DD-MM-YYYY HH:mm:ss} - {level} - {name}:{line} - {message}",
    level="DEBUG",
)