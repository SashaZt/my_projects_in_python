import os
import shutil
import logging
import time

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
no_archive_path = os.path.join(temp_path, "no_archive")
os.makedirs(temp_path, exist_ok=True)
os.makedirs(no_archive_path, exist_ok=True)

# Настройка логирования
log_file = "file_movement.log"

# Очистка лог-файла при каждом запуске
with open(log_file, "w"):
    pass

logging.basicConfig(
    filename=log_file,
    # level=logging.DEBUG, Для отладки
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Функция для поиска архива с таким же именем
def has_exact_archive(file_name, archive_names):
    file_base = file_name.lower()
    for archive_name in archive_names:
        archive_base = os.path.splitext(archive_name.lower())[0]
        logging.debug(f"Сравнение {file_base} с {archive_base}")
        if file_base == archive_base:
            return True
    return False


# Получаем список всех файлов в временной папке
all_files = os.listdir(temp_path)

# Список изображений и архивов
image_files = [f for f in all_files if f.lower().endswith((".jpg", ".jpeg", ".png"))]
archive_files = [f for f in all_files if f.lower().endswith((".zip", ".rar", ".7z"))]

logging.info(f"Найдено изображений: {len(image_files)}")
logging.info(f"Найдено архивов: {len(archive_files)}")

# Перемещение изображений без соответствующих архивов
for image_file in image_files:
    try:
        image_name, _ = os.path.splitext(image_file)
        logging.info(f"Обработка файла: {image_file}")
        if not has_exact_archive(image_name, archive_files):
            src = os.path.join(temp_path, image_file)
            dest = os.path.join(no_archive_path, image_file)
            shutil.move(src, dest)
            log_message = f"Перемещен {image_file} т.к. нету архива с таким же названием {image_name}"
            logging.info(log_message)
        else:
            log_message = f"{image_file} остался в {temp_path} т.к. существует архив с таким же названием"
            logging.info(log_message)
    except Exception as e:
        error_message = f"Ошибка при перемещении {image_file}: {e}"
        logging.error(error_message)

# Проверка изображений с похожими именами
for i, image_file1 in enumerate(image_files):
    for image_file2 in image_files[i + 1 :]:
        image_name1, ext1 = os.path.splitext(image_file1)
        image_name2, ext2 = os.path.splitext(image_file2)
        if image_name1.lower().replace(" ", "").replace(
            "-", ""
        ) == image_name2.lower().replace(" ", "").replace("-", ""):
            size1 = os.path.getsize(os.path.join(temp_path, image_file1))
            size2 = os.path.getsize(os.path.join(temp_path, image_file2))
            if size1 > size2:
                os.remove(os.path.join(temp_path, image_file2))
                log_message = (
                    f"Удален {image_file2} т.к. {image_file1} больше по размеру"
                )
                logging.info(log_message)
            else:
                os.remove(os.path.join(temp_path, image_file1))
                log_message = (
                    f"Удален {image_file1} т.к. {image_file2} больше по размеру"
                )
                logging.info(log_message)

print("Перемещение завершено. Логи записаны в файл file_movement.log.")
time.sleep(5)
