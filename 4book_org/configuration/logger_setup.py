import os
from loguru import logger

current_directory = os.getcwd()
logging_directory = "logging"
logging_path = os.path.join(current_directory, logging_directory)
os.makedirs(logging_path, exist_ok=True)

log_file_path = os.path.join(logging_path, "log_message.log")
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm} - {level} - {message}",
    level="DEBUG",
    encoding="utf-8",
)
