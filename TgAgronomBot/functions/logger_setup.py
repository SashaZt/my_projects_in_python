import os
from loguru import logger

current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
log_directory = os.path.join(temp_path, "log")
os.makedirs(log_directory, exist_ok=True)

log_file_path = os.path.join(log_directory, "log_message.log")
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
    level="DEBUG",
    encoding="utf-8",
)
