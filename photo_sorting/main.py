from pathlib import Path
import shutil
from configuration.logger_setup import logger  # Импортируем ваш настроенный логгер
from concurrent.futures import ThreadPoolExecutor, as_completed

# Путь к файлу с кодами и папкам с изображениями
kod_file = Path("kod.txt")
image_folder = Path("image")
found_folder = Path("found_photos")
not_found_folder = Path("not_found_photos")

# Создаем папки для найденных и ненайденных фото, если их нет
found_folder.mkdir(exist_ok=True)
not_found_folder.mkdir(exist_ok=True)

logger.info("Папки 'found_photos' и 'not_found_photos' подготовлены.")

# Читаем коды из файла и сохраняем их в множество для быстрого поиска
try:
    with kod_file.open("r") as f:
        codes = {line.strip() for line in f}
    logger.info(f"Загружено {len(codes)} кодов из файла {kod_file}.")
except Exception as e:
    logger.error(f"Ошибка при чтении файла {kod_file}: {e}")
    raise


# Создаем префиксное дерево (Trie) для кодов
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_code = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, code):
        node = self.root
        for char in code:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_code = True

    def search_prefix(self, filename):
        node = self.root
        code_prefix = ""
        for char in filename:
            if char in node.children:
                node = node.children[char]
                code_prefix += char
                if node.is_end_of_code:
                    return code_prefix
            else:
                break
        return None


# Инициализируем Trie и добавляем в него все коды
trie = Trie()
for code in codes:
    trie.insert(code)
logger.info("Префиксное дерево для кодов создано.")

# Списки для найденных и ненайденных кодов
found_codes = set()
not_found_codes = set()


# Функция для обработки файла изображения
def process_image_file(file_path):
    filename = file_path.name
    code_prefix = trie.search_prefix(filename)
    if code_prefix:
        destination = found_folder / filename
        shutil.move(str(file_path), str(destination))
        logger.info(f"Файл {filename} перемещен в {found_folder}.")
        return code_prefix
    else:
        destination = not_found_folder / filename
        shutil.move(str(file_path), str(destination))
        logger.info(f"Файл {filename} перемещен в {not_found_folder}.")
        return None


# Собираем все файлы изображений
image_files = list(image_folder.glob("*.jpg"))
logger.info(f"Найдено {len(image_files)} файлов изображений для обработки.")

# Используем ThreadPoolExecutor для многопоточной обработки файлов
logger.info("Запуск многопоточной обработки файлов изображений.")
try:
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {
            executor.submit(process_image_file, file_path): file_path
            for file_path in image_files
        }

        for future in as_completed(futures):
            code_prefix = future.result()
            if code_prefix:
                found_codes.add(code_prefix)
except Exception as e:
    logger.error(f"Ошибка при многопоточной обработке файлов: {e}")
    raise

# Определяем ненайденные коды
not_found_codes = codes - found_codes

# # Сохраняем список найденных кодов в файл found_photos.txt
# found_file_path = found_folder / "found_photos.txt"
# try:
#     with found_file_path.open("r") as found_file:
#         found_file.write("\n".join(found_codes))
#     logger.info(f"Список найденных кодов сохранен в файл {found_file_path}.")
# except Exception as e:
#     logger.error(f"Ошибка при записи файла {found_file_path}: {e}")
#     raise

# # Сохраняем список ненайденных кодов в файл not_found_photos.txt
# not_found_file_path = not_found_folder / "not_found_photos.txt"
# try:
#     with not_found_file_path.open("r") as not_found_file:
#         not_found_file.write("\n".join(not_found_codes))
#     logger.info(f"Список ненайденных кодов сохранен в файл {not_found_file_path}.")
# except Exception as e:
#     logger.error(f"Ошибка при записи файла {not_found_file_path}: {e}")
#     raise

logger.info("Списки успешно разделены и сохранены.")
