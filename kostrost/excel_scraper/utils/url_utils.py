import hashlib
import re
import urllib.parse

from config.logger import logger


def get_filename_from_url(url):
    """
    Формирует имя файла из URL (простой метод)

    Args:
        url: URL страницы

    Returns:
        Имя файла для сохранения HTML
    """
    # Очищаем URL от протокола и параметров
    clean_url = url.strip()

    # Создаем безопасное имя файла, заменяя все небуквенные символы на _
    filename = re.sub(r"[^a-zA-Z0-9]", "_", clean_url)

    # Ограничиваем длину имени файла
    if len(filename) > 100:
        filename = filename[:100]

    return f"{filename}.html"


def get_domain_filename_from_url(url):
    """
    Создает имя файла на основе домена и пути URL

    Args:
        url: URL страницы

    Returns:
        Имя файла для сохранения HTML в формате domain_path.html
    """
    try:
        # Парсинг URL
        parsed_url = urllib.parse.urlparse(url)

        # Получение домена без www
        domain = parsed_url.netloc.replace("www.", "")

        # Получение пути без ведущего слеша и замена всех / на _
        path = parsed_url.path.strip("/")
        if path:
            path = path.replace("/", "_")
            filename = f"{domain}_{path}.html"
        else:
            filename = f"{domain}.html"

        # Замена всех небуквенных символов на _
        filename = re.sub(r"[^\w\.-]", "_", filename)

        # Ограничение длины имени файла
        if len(filename) > 120:
            filename = filename[:120]

        return filename
    except Exception as e:
        logger.error(f"Ошибка при создании имени файла из URL {url}: {str(e)}")
        # Возвращаем запасной вариант имени файла
        return get_filename_from_url(url)


def get_hash_filename_from_url(url):
    """
    Создает имя файла на основе хеша URL

    Args:
        url: URL страницы

    Returns:
        Имя файла для сохранения HTML в формате hash.html
    """
    try:
        # Используем полный md5 хеш URL
        url_hash = hashlib.md5(url.encode()).hexdigest()

        # Формируем имя файла в формате hash.html
        filename = f"{url_hash}.html"

        return filename
    except Exception as e:
        logger.error(f"Ошибка при создании хеш-имени файла из URL {url}: {str(e)}")
        # Возвращаем запасной вариант имени файла
        return get_filename_from_url(url)
