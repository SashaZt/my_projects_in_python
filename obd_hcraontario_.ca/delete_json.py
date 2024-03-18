import os
import glob
import json


current_directory = os.getcwd()
temp_directory = "temp"
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
summary_path = os.path.join(temp_directory, "summary")
contact_path = os.path.join(temp_directory, "contact")

# Получаем список всех JSON файлов в папке
summary_files = glob.glob(os.path.join(contact_path, "*.json"))

# Проходим по всем файлам в списке
for summary_file in summary_files:
    try:
        # Открываем и загружаем содержимое файла
        with open(summary_file, "r", encoding="utf-8") as file:
            content = json.load(file)

        # Проверяем, пустой ли файл (содержит пустой список)
        if content == []:
            # Если файл пустой, удаляем его
            os.remove(summary_file)
            print(f"Удален пустой файл: {summary_file}")

    except json.JSONDecodeError as e:
        # В случае ошибки декодирования JSON выводим сообщение
        print(f"Ошибка чтения файла {summary_file}: {e}")
    except Exception as e:
        # Любые другие ошибки
        print(f"Ошибка обработки файла {summary_file}: {e}")
