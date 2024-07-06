from functions.check_chat import check_chat
from datetime import datetime
import logging

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Формат сообщения
    handlers=[
        logging.FileHandler("info.log", encoding="utf-8"),  # Запись в файл
    ],
)


def get_latest_chat_date():
    """
    Функция для получения последней даты чата с Mysql
    """
    sql_data = check_chat()
    if sql_data:
        latest_date_tuple = max(
            sql_data, key=lambda x: datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S")
        )
        latest_date = latest_date_tuple[1]  # Извлекаем дату из кортежа
    else:
        # Если sql_data пуст, устанавливаем latest_date в None или другое значение по умолчанию
        # Это значение можно использовать для проверки необходимости выполнения следующих шагов
        latest_date = None
        logging.info("Нет данных для обработки. Продолжаем выполнение скрипта.")
    logging.info(f"Последняя дата в БД {latest_date}")
    return latest_date
