from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_page_directory = current_directory / "html_page"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_page_directory.mkdir(parents=True, exist_ok=True)

csv_output_file = current_directory / "output.csv"


# Функция для чтения городов из CSV файла


def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def save_to_csv(href_set):
    # Создаем DataFrame из уникальных ссылок
    df = pd.DataFrame(href_set, columns=["url"])
    # Сохраняем DataFrame в CSV файл
    df.to_csv(csv_output_file, index=False, encoding="utf-8")
    logger.info(f"Данные успешно сохранены в {csv_output_file}")


def get_url():

    all_urls = read_cities_from_csv(csv_output_file)  # Чтение URL из CSV файла

    for url in all_urls:  # Ограничено одной URL для теста
        html_company = html_files_directory / f"{url.split('/')[-1]}.html"

        if html_company.exists():
            logger.warning(f"Файл {html_company} уже существует, пропускаем.")
            continue  # Переходим к следующей итерации цикла
        payload = {"api_key": API_KEY, "url": url}
        r = requests.get(
            "https://api.scraperapi.com/",
            params=payload,
            timeout=30,
        )
        if r.status_code == 200:
            with open(html_company, "w", encoding="utf-8") as file:
                file.write(r.text)
            logger.info(html_company)
        else:
            logger.info(r.status_code)


# def get_page_html():
#     max_page = None
#     url_start = "https://allegro.pl/kategoria/narzedzia-mlotowiertarki-147650?price_from=200&price_to=800&stan=nowe"

#     html_company = html_page_directory / "url_start.html"
#     payload = {"api_key": API_KEY, "url": url_start}
#     if html_company.exists():
#         logger.warning(f"Файл {html_company} уже существует, пропускаем.")
#     else:
#         r = requests.get(
#             "https://api.scraperapi.com/",
#             params=payload,
#             timeout=30,
#         )

#         if r.status_code == 200:
#             src = r.text
#             with open(html_company, "w", encoding="utf-8") as file:
#                 file.write(src)
#             soup = BeautifulSoup(src, "lxml")
#             # Находим div с атрибутом data-box-name="pagination top"
#             pagination_div = soup.find("div", {"aria-label": "paginacja"})
#             # Находим первый span внутри найденного div и проверяем, что это элемент BeautifulSoup
#             if pagination_div:
#                 span_element = pagination_div.find("span")
#                 if span_element and isinstance(span_element, str) == False:
#                     max_page_text = span_element.get_text(
#                         strip=True
#                     )  # Извлечение текста с удалением пробелов
#                     max_page = int(max_page_text)
#                 else:
#                     logger.error(
#                         "Элемент span не найден или не является объектом BeautifulSoup"
#                     )
#             else:
#                 logger.error("Элемент div с aria-label='paginacja' не найден")
#             logger.info(html_company)
#         else:
#             logger.info(r.status_code)
#     for page in range(2, max_page + 1):
#         html_company = html_page_directory / f"url_start_{page}.html"
#         payload = {"api_key": API_KEY, "url": f"{url_start}&p={page}"}
#         if html_company.exists():
#             logger.warning(f"Файл {html_company} уже существует, пропускаем.")
#         else:
#             r = requests.get(
#                 "https://api.scraperapi.com/",
#                 params=payload,
#                 timeout=30,
#             )
#             src = r.text
#             with open(html_company, "w", encoding="utf-8") as file:
#                 file.write(src)


def get_all_page_html(url_start):

    html_company = html_page_directory / "url_start.html"
    payload = {"api_key": API_KEY, "url": url_start}

    # Проверяем, существует ли уже файл первой страницы
    if html_company.exists():
        logger.warning(f"Файл {html_company} уже существует, пропускаем загрузку.")
        max_page = parsin_page()  # Получаем max_page из существующего файла
    else:
        # Запрос к API для первой страницы
        r = requests.get("https://api.scraperapi.com/", params=payload, timeout=60)

        if r.status_code == 200:
            src = r.text
            with open(html_company, "w", encoding="utf-8") as file:
                file.write(src)
            max_page = (
                parsin_page()
            )  # Получаем max_page из только что сохраненного файла
            logger.info(f"Сохранена первая страница: {html_company}")
        else:
            logger.error(f"Ошибка при запросе первой страницы: {r.status_code}")
            return  # Если запрос не успешен, выходим из функции

    # Запрашиваем страницы с 2 по max_page, если max_page определен
    if max_page:
        for page in range(2, max_page + 1):
            html_company = html_page_directory / f"url_start_{page}.html"
            # Обновляем payload для каждой страницы
            payload = {"api_key": API_KEY, "url": f"{url_start}&p={page}"}

            if html_company.exists():
                logger.warning(f"Файл {html_company} уже существует, пропускаем.")
            else:
                r = requests.get(
                    "https://api.scraperapi.com/", params=payload, timeout=60
                )

                if r.status_code == 200:
                    src = r.text
                    with open(html_company, "w", encoding="utf-8") as file:
                        file.write(src)
                    logger.info(f"Сохранена страница {page}: {html_company}")
                else:
                    logger.error(f"Ошибка при запросе страницы {page}: {r.status_code}")


def parsin_page():
    max_page = None
    html_company = html_page_directory / "url_start.html"

    # Открываем локально сохранённый файл первой страницы
    with open(html_company, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")

    # Находим div с атрибутом aria-label="paginacja"
    pagination_div = soup.find("div", {"aria-label": "paginacja"})

    # Извлекаем максимальное количество страниц
    if pagination_div:
        span_element = pagination_div.find("span")
        if span_element:
            try:
                max_page_text = span_element.get_text(strip=True)
                max_page = int(max_page_text)
            except ValueError:
                logger.error("Не удалось преобразовать max_page_text в число")
        else:
            logger.error(
                "Элемент span не найден или не является объектом BeautifulSoup"
            )
    else:
        logger.error("Элемент div с aria-label='paginacja' не найден")

    return max_page


if __name__ == "__main__":
    url_start = "https://allegro.pl/kategoria/narzedzia-mlotowiertarki-147650?price_from=200&price_to=800&stan=nowe"
    # get_all_page_html(url_start)
    parsin_page()
