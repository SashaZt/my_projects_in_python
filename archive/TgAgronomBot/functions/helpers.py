from loguru import logger


def read_keywords(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            keywords = [line.strip() for line in file if line.strip()]
        return keywords
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден.")
        return []


def read_list_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            items = [line.strip() for line in file if line.strip()]
        return items
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден.")
        return []
