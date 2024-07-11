import os
import shutil
import time
from loguru import logger

logger.add(
    "info.log",
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",  # Формат сообщения
    level="DEBUG",  # Уровень логирования
    encoding="utf-8",  # Кодировка
    mode="w",  # Перезапись файла при каждом запуске
)


def move_authorization_file():
    # Определение пути к папке загрузок текущего пользователя
    user_downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    source_file_path = os.path.join(user_downloads_folder, "authorization.json")

    # Определение пути к текущей директории
    destination_file_path = os.path.join(os.getcwd(), "authorization.json")

    # Проверка существования исходного файла
    if not os.path.exists(source_file_path):
        logger.info(f"Файл {source_file_path} не найден.")
        return

    # Проверка доступа к файлу
    def is_file_accessible(filepath, mode="r"):
        try:
            with open(filepath, mode):
                pass
        except IOError:
            return False
        return True

    # Функция для удаления файла, если он существует
    def remove_existing_file(filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

    # Повторные попытки копирования файла
    for attempt in range(10):
        if is_file_accessible(source_file_path, "r"):
            try:
                remove_existing_file(destination_file_path)
                shutil.copy(source_file_path, destination_file_path)
                logger.info(
                    f"Файл скопирован из {source_file_path} в {destination_file_path}"
                )

                # Удаление исходного файла после успешного копирования
                os.remove(source_file_path)
                logger.info(f"Исходный файл {source_file_path} удален.")
                return
            except PermissionError as e:
                logger.info(
                    f"Попытка {attempt+1}: Файл занят другим процессом. Ожидание..."
                )
                time.sleep(1)
            except Exception as e:
                logger.info(f"Попытка {attempt+1}: Произошла ошибка: {e}. Ожидание...")
                time.sleep(1)
        else:
            logger.info(
                f"Попытка {attempt+1}: Файл {source_file_path} недоступен для чтения. Ожидание..."
            )
            time.sleep(1)

    logger.info(f"Не удалось скопировать файл {source_file_path} после 10 попыток.")


def start_file_check():
    move_authorization_file()
