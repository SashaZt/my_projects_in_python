from loguru import logger
from pathlib import Path
from dotenv import dotenv_values


env_values = dotenv_values(".env")
log_directory = Path(env_values["LOG_PATH"])

log_file_path = Path(log_directory, "log_message.log")
logger.add(
    log_file_path,
    format="{time:DD-MM-YYYY HH:mm:ss} - {level} - {name}:{line} - {message}",
    level="DEBUG",
    encoding="utf-8",
)
