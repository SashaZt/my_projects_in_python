import requests
import re
import requests
from configuration.logger_setup import logger
import random
from bs4 import BeautifulSoup
from pathlib import Path
import os
import csv
import threading
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
csv_file_successful = data_directory / "identifier_successful.csv"

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    # logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    retry=retry_if_exception_type(requests.RequestException),
)
def get_html(url, proxies_dict):
    response = requests.get(
        url,
        headers=headers,
        proxies=proxies_dict,
        timeout=10,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        return response.text
    else:
        logger.error(response.status_code)


def read_urls_from_csv() -> list:
    # Чтение CSV файла с помощью pandas
    df = pd.read_csv(output_csv_file)

    # Проверяем, есть ли в файле колонка 'url'
    if "url" in df.columns:
        # Возвращаем список URL
        return df["url"].dropna().tolist()
    else:
        raise ValueError("В файле отсутствует колонка 'url'.")


def parsing():
    urls = read_urls_from_csv()
    proxies = load_proxies()  # Загружаем список всех прокси
    for url in urls:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
        src = get_html(url, proxies_dict)
        if src is None:
            logger.info(url)
            continue  # Пропускаем, если не удалось получить HTML

        soup = BeautifulSoup(src, "lxml")

        # Список для хранения всех единиц данных
        all_results = []
        breadcrumb_parts = []
        table_breadcrumbs = soup.find("div", attrs={"class": "breadcrumbs"})
        if table_breadcrumbs:
            all_itemListElement = table_breadcrumbs.find_all(
                "div", attrs={"itemprop": "itemListElement"}
            )
            for item in all_itemListElement[1:]:
                folder_item = item.get_text(strip=True)
                breadcrumb_parts.append(folder_item)
        name = soup.find("h1", attrs={"itemprop": "name"}).get_text(strip=True)
        breadcrumb_parts.append(name)
        # Начинаем с текущей директории
        current_path = current_directory

        # Создаем базовые вложенные папки
        for part in breadcrumb_parts:
            current_path = current_path / part  # Строим путь к вложенной папке
            current_path.mkdir(
                parents=True, exist_ok=True
            )  # Создаем папку, если ее нет

        # Теперь current_path указывает на директорию 'current_directory\ГДЗ\8 клас\Німецька мова'

        # Найти все accordion-group элементы
        accordion_groups = soup.find_all("div", class_="accordion-group")

        for group in accordion_groups:
            # Найти заголовок теста или раздела
            panel_title_elem = group.find("div", class_="panel-title-elem")

            if panel_title_elem:
                # Получаем название теста, например, "Test 1 (Lektion 1)"
                test_name = panel_title_elem.get_text(strip=True)
                cleaned_path_ = re.sub(r"[^а-яА-ЯіІїЇєЄґҐ0-9]", "_", test_name)

                # Убираем несколько подчеркиваний подряд
                cleaned_path_ = re.sub(r"_+", "_", cleaned_path_)

                # Убираем подчеркивания в начале и конце строки
                cleaned_path_ = cleaned_path_.strip("_")

                # Ограничиваем длину пути до допустимых 40 символов
                max_length = 40
                cleaned_path_ = cleaned_path_[:max_length]

                # Создаем папку для теста внутри уже построенного пути
                test_directory = current_path / cleaned_path_
                test_directory.mkdir(parents=True, exist_ok=True)

                # Найти все варианты внутри теста
                accordion_body = group.find("div", class_="accordion-body")
                if accordion_body:
                    variant_links = accordion_body.find_all("a")

                    for link in variant_links:
                        # Получаем название варианта, например, "Вариант 1"
                        variant_name_span = link.find("span")
                        if variant_name_span:
                            variant_name = variant_name_span.get_text(strip=True)
                            cleaned_path = re.sub(
                                r"[^а-яА-ЯіІїЇєЄґҐ0-9]", "_", variant_name
                            )

                            # Убираем несколько подчеркиваний подряд
                            cleaned_path = re.sub(r"_+", "_", cleaned_path)

                            # Убираем подчеркивания в начале и конце строки
                            cleaned_path = cleaned_path.strip("_")

                            # Ограничиваем длину пути до допустимых 40 символов
                            cleaned_path = cleaned_path[:max_length]

                            # Создаем папку для варианта внутри папки теста
                            variant_directory = test_directory / cleaned_path
                            variant_directory.mkdir(parents=True, exist_ok=True)

                            # Сохраняем ссылку в файле 'url.txt' внутри папки варианта
                            variant_url = f"https://4book.org{link['href']}"
                            with open(
                                variant_directory / "url.txt", "w", encoding="utf-8"
                            ) as f:
                                f.write(variant_url)
            else:
                # Если панель теста отсутствует, пытаемся найти ссылки на разделы вроде Lexik или Grammatik
                section_link = group.find("a")

                if section_link:
                    # Проверка на наличие тега <span> внутри ссылки
                    section_name_span = section_link.find("span")
                    if section_name_span:
                        # Получаем название раздела, например, "Lexik (I. Semester)"
                        section_name = section_name_span.get_text(strip=True)
                        # Убираем все символы, кроме украинских букв (кириллица) и цифр
                        cleaned_path = re.sub(
                            r"[^а-яА-ЯіІїЇєЄґҐ0-9]", "_", section_name
                        )

                        # Убираем несколько подчеркиваний подряд
                        cleaned_path = re.sub(r"_+", "_", cleaned_path)

                        # Убираем подчеркивания в начале и конце строки
                        cleaned_path = cleaned_path.strip("_")

                        # Ограничиваем длину пути до допустимых 40 символов
                        cleaned_path = cleaned_path[:max_length]

                        # Создаем папку для раздела внутри уже построенного пути
                        section_directory = current_path / cleaned_path
                        section_directory.mkdir(parents=True, exist_ok=True)

                        # Сохраняем ссылку в файле 'url.txt' внутри папки раздела
                        section_url = f"https://4book.org{section_link['href']}"
                        with open(
                            section_directory / "url.txt", "w", encoding="utf-8"
                        ) as f:
                            f.write(section_url)


def find_gdz_directory(directory: Path) -> Path:
    # Поиск папки "ГДЗ" в текущей директории
    for item in directory.iterdir():
        if item.is_dir() and item.name == "ГДЗ":
            return item
    return None


@retry(
    stop=stop_after_attempt(10),
    wait=wait_fixed(10),
    retry=retry_if_exception_type(
        (requests.RequestException, requests.exceptions.ProxyError)
    ),
)
def process_directory(directory: Path):

    # Рекурсивный обход папок
    proxies = load_proxies()  # Загружаем список всех прокси

    for root, dirs, files in os.walk(directory):

        current_dir = Path(root)

        # Проверяем наличие файла url.txt
        if "url.txt" in files:
            url_file_path = current_dir / "url.txt"
            urls_file_path = current_dir / "all_url.txt"
            if urls_file_path.exists():
                continue
            else:
                # logger.info(f"Папка {url_file_path}")

                # Чтение ссылки из url.txt
                with open(url_file_path, "r") as f:
                    urls = f.readlines()  # Чтение всех строк в список
                for url in urls:

                    url = url.strip()  # Убираем лишние пробелы и символы новой строки
                    proxy = random.choice(proxies)  # Выбираем случайный прокси
                    proxies_dict = {"http": proxy, "https": proxy}
                    # logger.info(url)
                    # Делаем запрос по ссылке
                    response = requests.get(
                        url,
                        headers=headers,
                        proxies=proxies_dict,
                        timeout=60,
                    )
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "lxml")

                        # Ищем нужный элемент с классом 'row list-task'
                        task_rows = soup.find("div", class_="row list-task")
                        if task_rows:
                            # Извлекаем все ссылки href
                            links = task_rows.find_all("a", class_="btn1")
                            new_urls = [
                                f"https://4book.org{link['href']}" for link in links
                            ]

                            # Перезаписываем url.txt новыми ссылками
                            with open(urls_file_path, "w") as f:
                                for new_url in new_urls:
                                    f.write(new_url + "\n")

                            logger.info(f"Сохранил {urls_file_path}")

                    else:
                        logger.error(
                            f"Ошибка при запросе {url}: статус {response.status_code}"
                        )


def write_to_csv(data, filename):
    write_lock = threading.Lock()
    # Проверяем, существует ли файл
    file_path = Path(filename)
    header_written = False
    with write_lock:  # Используем блокировку для защиты кода записи в файл
        # Проверка на необходимость добавления заголовка
        if not header_written:
            if not file_path.exists() or file_path.stat().st_size == 0:
                with open(filename, "a", encoding="utf-8") as f:
                    f.write("url\n")
            header_written = True  # Устанавливаем флаг после добавления заголовка

        # Проверяем, является ли `data` итерируемым (множеством, списком) или одиночным значением
        if isinstance(data, (set, list, tuple)):
            urls_to_write = data
        else:
            urls_to_write = [data]  # Преобразуем одиночный URL в список

        # Записываем каждый URL в новую строку CSV-файла
        with open(filename, "a", encoding="utf-8") as f:
            for url in urls_to_write:
                f.write(f"{url}\n")


def get_successful_urls():
    # Загружаем уже обработанные идентификаторы из CSV-файла
    if not Path(csv_file_successful).exists():
        return set()

    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        successful_urls = {
            row[0]
            for idx, row in enumerate(reader)
            if row and idx > 0  # Пропускаем заголовок
        }  # Собираем идентификаторы в множество
    return successful_urls


@retry(
    stop=stop_after_attempt(50),
    wait=wait_fixed(10),
    retry=retry_if_exception_type(Exception),
)
def download_image(img_url, number_task, current_dir, headers):
    proxies = load_proxies()  # Загружаем список всех прокси
    max_retries = len(
        proxies
    )  # Устанавливаем количество попыток равным количеству прокси

    # Проверка на относительный URL
    if img_url.startswith("/"):
        img_url = f"https://4book.org{img_url}"

    # Полный путь к файлу
    file_path = os.path.join(current_dir, f"{number_task}.jpg")

    # Проверяем, существует ли уже файл
    if os.path.exists(file_path):
        logger.info(f"Файл {file_path} уже существует. Пропускаем загрузку.")
        return

    for attempt in range(max_retries):
        proxy = proxies[attempt]  # Выбираем прокси по индексу попытки
        proxies_dict = {"http": proxy, "https": proxy}

        try:
            # Загружаем изображение
            img_response = requests.get(
                img_url, headers=headers, proxies=proxies_dict, timeout=60
            )
            if img_response.status_code == 200:
                # Сохраняем изображение в файл
                with open(file_path, "wb") as f:
                    f.write(img_response.content)
                logger.info(f"Изображение {number_task}.jpg сохранено в {file_path}")
                return  # Если успешно, выходим из функции
            else:
                logger.error(
                    f"Ошибка загрузки изображения {img_url} через прокси {proxy}: статус {img_response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Ошибка при загрузке изображения {img_url} через прокси {proxy}: {str(e)}"
            )

        # Если попытка не удалась, переходим к следующему прокси
        logger.info(
            f"Попытка {attempt + 1}/{max_retries} не удалась. Пробуем следующий прокси..."
        )

    # Если все попытки исчерпаны и изображение не загружено
    logger.error(
        f"Не удалось загрузить изображение {img_url} после {max_retries} попыток."
    )


@retry(
    stop=stop_after_attempt(50),
    wait=wait_fixed(10),
    retry=retry_if_exception_type(Exception),
)
def process_directory_img(directory: Path):
    fetch_lock = threading.Lock()
    # Заголовки, которые используются в curl запросе
    successful_urls = get_successful_urls()
    proxies = load_proxies()  # Загружаем список всех прокси
    max_retries = len(
        proxies
    )  # Устанавливаем количество попыток равным количеству прокси

    # Рекурсивный обход папок
    for root, dirs, files in os.walk(directory):

        current_dir = Path(root)

        # Проверяем наличие файла url.txt
        if "all_url.txt" in files:
            url_file_path = current_dir / "all_url.txt"
            logger.info(f"Идем в папку {url_file_path}")
            # Чтение ссылки из url.txt
            with open(url_file_path, "r", encoding="utf-8") as f:
                urls = f.readlines()  # Чтение всех строк в список
            # Обрабатываем каждый URL в цикле
            for url in urls:
                url = url.strip()  # Убираем лишние пробелы и символы новой строки

                if url:  # Проверяем, что строка не пустая
                    if url in successful_urls:
                        logger.error("| Компания уже была обработана, пропускаем. |")
                        continue
                    for attempt in range(max_retries):
                        proxy = proxies[attempt]  # Выбираем прокси по индексу попытки
                        proxies_dict = {"http": proxy, "https": proxy}
                        try:
                            response = requests.get(
                                url,
                                headers=headers,
                                proxies=proxies_dict,
                                timeout=60,
                            )
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.text, "lxml")

                                number_task = None
                                # Извлечение номера задачи
                                number_task_raw = soup.find(
                                    "span", class_="number-task"
                                )

                                if number_task_raw:
                                    number_task = number_task_raw.get_text(strip=True)
                                    # logger.info(f"Номер задачи: {number_task}")
                                else:
                                    logger.error("Номер задачи не найден на странице.")
                                    continue

                                # Поиск изображения
                                img_container = soup.find(
                                    "div",
                                    class_=re.compile(
                                        r"img-content.*js-img-content.*js-img-answer"
                                    ),
                                )

                                if img_container:
                                    # Находим тег <img> внутри контейнера
                                    img_tag = img_container.find("img")

                                    if img_tag and img_tag.get("src"):
                                        img_url = img_tag.get("src")

                                        if img_url and number_task:
                                            # Полный путь к файлу
                                            file_path = os.path.join(
                                                current_dir, f"{number_task}.jpg"
                                            )

                                            # Проверяем, существует ли файл
                                            if os.path.exists(file_path):
                                                with fetch_lock:
                                                    # Добавляем идентификатор в множество успешных
                                                    successful_urls.add(url)
                                                write_to_csv(url, csv_file_successful)
                                                continue
                                                # logger.info(
                                                # f"Файл {file_path} уже существует. Пропускаем скачивание."
                                                # )
                                            else:
                                                # Скачиваем изображение
                                                download_image(
                                                    img_url,
                                                    number_task,
                                                    current_dir,
                                                    headers,
                                                )
                                                with fetch_lock:
                                                    # Добавляем идентификатор в множество успешных
                                                    successful_urls.add(url)
                                                write_to_csv(url, csv_file_successful)
                                else:
                                    logger.error("Изображение не найдено на странице.")

                            else:
                                logger.error(
                                    f"Ошибка запроса {url}: статус {response.status_code}"
                                )
                        except:
                            logger.error(url)


def process_final(directory: Path):
    # Рекурсивный обход всех папок начиная с указанной директории
    for root, dirs, files in os.walk(directory):
        current_dir = Path(root)  # Преобразование текущего пути к объекту Path

        # Проверяем наличие файла all_url.txt в текущей папке
        if "all_url.txt" in files:
            url_file_path = (
                current_dir / "all_url.txt"
            )  # Формируем полный путь к файлу all_url.txt

            # Укорачиваем путь к текущей директории, начиная с директории поиска
            relative_dir = current_dir.relative_to(directory)

            # Чтение ссылок из all_url.txt и подсчет количества строк
            with open(url_file_path, "r") as f:
                urls = f.readlines()  # Чтение всех строк в список
                num_urls = len(urls)  # Подсчет количества строк (URL)

            # Подсчет количества JPG файлов в текущей папке
            # Создаем список всех файлов с расширением .jpg (без учета регистра)
            jpg_files = [file for file in files if file.lower().endswith(".jpg")]
            num_jpg_files = len(jpg_files)  # Получаем количество JPG файлов

            # Сравниваем количество строк в all_url.txt с количеством JPG файлов
            if num_urls != num_jpg_files:
                # Логирование, если количество URL и JPG файлов не совпадает
                logger.warning(
                    f"Папка: {relative_dir}, Количество URL: {num_urls}, Количество JPG файлов: {num_jpg_files} - Не совпадает!"
                )

        # Удаление всех файлов с расширением .txt в текущей папке
        txt_files = [file for file in files if file.lower().endswith(".txt")]
        for txt_file in txt_files:
            txt_file_path = current_dir / txt_file
            try:
                os.remove(txt_file_path)  # Удаление файла
                logger.info(f"Удален файл: {txt_file_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении файла {txt_file_path}: {e}")


def generate_tree(directory: Path, output_file: Path):
    with open(output_file, "w", encoding="utf-8") as f:
        # Рекурсивный обход всех папок начиная с указанной директории
        for root, dirs, files in os.walk(directory):
            current_dir = Path(root)  # Преобразование текущего пути к объекту Path
            # Формируем уровень вложенности для отображения структуры дерева
            level = len(current_dir.relative_to(directory).parts)
            indent = "    " * level
            # Записываем текущую папку в файл
            f.write(f"{indent}{current_dir.name}\n")

            # Если текущая папка является конечной (нет поддиректорий), записываем файлы внутри
            if not dirs:
                file_indent = "    " * (level + 1)
                for file in files:
                    if file.lower().endswith(".jpg"):
                        f.write(f"{file_indent}{file}\n")


def main():
    # parsing()
    gdz_directory = find_gdz_directory(current_directory)

    if gdz_directory:
        logger.info(f"Найдена папка: {gdz_directory}")
        # process_directory(gdz_directory)

        # process_directory_img(gdz_directory)
        # process_final(gdz_directory)
        output_file = Path("output.txt")

        generate_tree(gdz_directory, output_file)
    # else:
    #     logger.error("Папка 'ГДЗ' не найдена в текущей директории")


if __name__ == "__main__":
    main()
