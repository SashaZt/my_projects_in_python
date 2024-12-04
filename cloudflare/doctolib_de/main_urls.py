from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

# Путь к файлам
data_directory = Path.cwd() / "data"
data_directory.mkdir(parents=True, exist_ok=True)

all_urls_page = data_directory / "all_urls.csv"
new_urls_page = data_directory / "new_urls.csv"


# Функция для чтения CSV
def read_csv(file):
    """
    Читает файл CSV и возвращает список URL.
    """
    df = pd.read_csv(file)
    return df["url"].tolist()


# Функция для фильтрации URL
def filter_urls(urls):
    """
    Фильтрует URL-адреса, оставляя только те, где после домена три или более сегментов пути.
    """
    valid_urls = []
    for url in urls:
        path = urlparse(url).path
        path_segments = path.strip("/").split("/")
        if len(path_segments) > 2:  # Проверка на 3 или более сегментов
            valid_urls.append(url)
    return valid_urls


# Функция для записи в CSV
def write_csv(file, urls):
    """
    Записывает список URL в файл CSV.
    """
    df = pd.DataFrame({"url": urls})
    df.to_csv(file, index=False, encoding="utf-8")
    print(f"Сохранено: {file}")


# Основной процесс
def process_urls():
    """
    Читает URL из файла, фильтрует их и сохраняет результат в новый файл.
    """
    # Читаем все URL из исходного файла
    all_urls = read_csv(all_urls_page)
    print(f"Прочитано URL: {len(all_urls)}")

    # Фильтруем URL
    filtered_urls = filter_urls(all_urls)
    print(f"Подходящих URL: {len(filtered_urls)}")

    # Сохраняем в новый файл
    write_csv(new_urls_page, filtered_urls)


if __name__ == "__main__":
    process_urls()
