# Обработка для замены ссылов в файлах
import os
from configuration.logger_setup import logger


def find_and_process_index_files(
    start_directory: str, search_text: str, replace_text: str
):
    # Рекурсивно обходим все подкаталоги, начиная с указанной директории
    for root, dirs, files in os.walk(start_directory):
        for file in files:
            if file == "index.html":
                file_path = os.path.join(root, file)
                replace_text_in_file(file_path, search_text, replace_text)


def replace_text_in_file(file_path: str, search_text: str, replace_text: str):
    # Открываем файл и читаем его содержимое
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    # Проверяем, есть ли искомый текст в файле
    if search_text in file_content:
        # Заменяем текст
        new_content = file_content.replace(search_text, replace_text)

        # Сохраняем изменения в файл
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(new_content)

        # Логируем файл, в котором была произведена замена
        logger.info(f"Updated file: {file_path}")


# Основной код для выполнения всех шагов
start_directory = "C:\\my_projects_in_python\\vOvA\\www"
search_text = "/ru/"
replace_text = "/en/"

find_and_process_index_files(start_directory, search_text, replace_text)
