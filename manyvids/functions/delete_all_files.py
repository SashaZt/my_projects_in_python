from functions.directories import create_temp_directories
import glob
import os
import shutil

current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
cookies_path = os.path.join(temp_path, "cookies")
login_pass_path = os.path.join(temp_path, "login_pass")
daily_sales_path = os.path.join(temp_path, "daily_sales")
monthly_sales_path = os.path.join(temp_path, "monthly_sales")
payout_history_path = os.path.join(temp_path, "payout_history")
pending_custom_path = os.path.join(temp_path, "pending_custom")
chat_path = os.path.join(temp_path, "chat")


def delete_all_files():
    """
    Функция для удаления временных файлов по всем папкам
    """
    all_path = [chat_path, daily_sales_path, payout_history_path, pending_custom_path]

    for path in all_path:
        # Проверяем, является ли путь директорией
        if os.path.isdir(path):
            print(f"Удаление содержимого из директории: {path}")
            # Выводим содержимое директории перед удалением
            for root, dirs, files in os.walk(path):
                for name in files:
                    print(f"Файл для удаления: {os.path.join(root, name)}")
                for name in dirs:
                    print(f"Поддиректория для удаления: {os.path.join(root, name)}")

            # Удаляем все содержимое директории
            shutil.rmtree(path)
            # Пересоздаем пустую директорию
            os.makedirs(path)
            print(
                f"Все файлы и директории в {path} были удалены и директория пересоздана."
            )
        else:
            print(f"Директория не найдена: {path}")
