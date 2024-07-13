import os
from datetime import datetime
import schedule
import time
from loguru import logger
from functions.get_asio import get_asio
from functions.get_sql_data_day import get_sql_data_day
from functions.get_sql_payout_history import get_sql_payout_history
from functions.get_sql_chat import get_sql_chat
from functions.get_table_01_to_google import get_table_01_to_google
from functions.get_table_03_to_google import get_table_03_to_google
from functions.get_table_04_to_google import get_table_04_to_google
from functions.get_pending_to_google import get_pending_to_google
from functions.unique_users_to_sql import unique_users_to_sql
from functions.delete_all_files import delete_all_files
from functions.directories import create_temp_directories
from functions.data_exchange import main_exchange


current_directory = os.getcwd()
paths = create_temp_directories(current_directory)

# Теперь можно использовать пути из словаря `paths`
cookies_path = paths["cookies_path"]
login_pass_path = paths["login_pass_path"]
daily_sales_path = paths["daily_sales_path"]
monthly_sales_path = paths["monthly_sales_path"]
payout_history_path = paths["payout_history_path"]
pending_custom_path = paths["pending_custom_path"]
chat_path = paths["chat_path"]


# Настройка базовой конфигурации логирования
logger.remove()  # Удаляем все ранее добавленные обработчики
logger.add(
    "info.log",
    format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",  # Формат сообщения
    level="DEBUG",  # Уровень логирования
    encoding="utf-8",  # Кодировка
    mode="w",  # Перезапись файла при каждом запуске
)

# Пример логирования
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")


def job():
    log_filename = "log.txt"
    if os.path.exists(log_filename):
        os.remove(log_filename)

    now = datetime.now()  # Текущие дата и время
    month = str(now.month)
    filterYear = str(now.year)
    currentTime = now.strftime("%H:%M:%S")  # Форматирование текущего времени

    logger.info(
        f"[{currentTime}] Запуск задачи для месяца {month} и года {filterYear}."
    )
    get_asio()
    get_sql_data_day()
    get_sql_payout_history()
    get_sql_chat()
    get_table_01_to_google()
    get_table_03_to_google()
    get_table_04_to_google()
    get_pending_to_google()
    unique_users_to_sql()
    delete_all_files()
    # main_exchange()

    logger.info(f"Все выполнено, ждем 30мин")


job()

schedule.every(30).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
