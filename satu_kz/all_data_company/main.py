import json
from pathlib import Path
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
import csv

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_directory = current_directory / "html"
csv_directory = current_directory / "csv"
configuration_directory = current_directory / "configuration"
# Пути к файлам
output_csv_file = current_directory / "urls.csv"
# Создание директорий, если их нет
html_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "referer": "https://oil-market.kz/product_list/page_46?product_items_per_page=48",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def get_html_product_list(url, max_retries=10, delay=5):
    """
    Получение HTML-страницы списка продуктов с обработкой повторных запросов.

    :param url: str - Базовый URL
    :param headers: dict - Заголовки для запроса
    :param max_retries: int - Максимальное количество попыток
    :param delay: int - Задержка между попытками (в секундах)
    :return: str или None - HTML содержимое или None, если не удалось получить данные
    """
    retries = 0  # Счётчик попыток

    while retries < max_retries:
        try:
            response = requests.get(
                f"{url}/product_list",
                headers=headers,
                timeout=30,
            )

            # Проверка кода ответа
            if response.status_code == 200:
                content = response.text
                logger.info(f"Успешный запрос: статус {response.status_code}")
                return content
            elif response.status_code == 404:
                return None
            else:
                retries += 1
                logger.error(f"Попытка {retries}/{max_retries}: статус {response.status_code}. Повтор через {delay} секунд...")
                time.sleep(delay)

        except requests.RequestException as e:
            retries += 1
            logger.error(
                f"Попытка {retries}/{max_retries}. Ошибка: {e}. Повтор через {delay} секунд...")
            time.sleep(delay)

    # Если все попытки исчерпаны
    logger.error(f"Не удалось получить HTML после {max_retries} попыток.")
    return None


def get_product_count(soup):
    script_tags = soup.find_all('script', {'type': 'application/ld+json'})

    # Счётчик объектов типа Product
    product_count = 0
    product_names = []

    for script in script_tags:
        try:
            # Парсить содержимое JSON
            data = json.loads(script.string)

            # Если это объект, а не массив
            if isinstance(data, dict) and data.get('@type') == 'Product':
                product_count += 1
                product_names.append(data.get('name', 'No Name'))
            # Если это массив или содержит вложенный объект
            elif isinstance(data, dict) and '@graph' in data:
                product_count += sum(1 for item in data['@graph'] if item.get('@type') == 'Product')
                roduct_names.append(item.get('name', None))
        except json.JSONDecodeError:
            # Игнорировать ошибки, если содержимое не валидное JSON
            continue
    return int(product_count),product_names[:3]


def paginator(soup):
    # Найти div с атрибутом data-bazooka="Paginator"
    pagination_div = soup.find('div', {'data-bazooka': 'Paginator'})
    # Количество страниц
    pages_count = None
    # Количество товаров на странице
    per_page = None
    # Проверка и извлечение данных
    if pagination_div:
        pages_count = int(pagination_div.get('data-pagination-pages-count'))
        per_page = int(pagination_div.get('data-pagination-per-page'))
        return pages_count, per_page
        # # Логирование с корректным выводом
        # logger.info(f"Количество страниц (data-pagination-pages-count): {pages_count}")
        # logger.info(f"Количество элементов на странице (data-pagination-per-page): {pages_count}")
    else:
        return pages_count, per_page


def get_total_products(url):

    content = get_html_product_list(url)
    # Пройтись по каждому HTML файлу в папке
    # for html_file in html_directory.glob("*.html"):
    #     with html_file.open(encoding="utf-8") as file:
    #         content = file.read()
    if content is not None:
        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        # Количество товароа на странице
        product_count, product_names = get_product_count(soup)
        pages_count, per_page = paginator(soup)
        # Количество товароа на последней странице
        product_count_last_page = None
        if pages_count is not None and pages_count > 1:
            product_count_last_page = get_last_page(url, pages_count)
        # Убедитесь, что переменные имеют значения или установите их по умолчанию
        product_count = product_count or 0  # Если None, установить в 0
        pages_count = pages_count or 0      # Если None, установить в 0
        product_count_last_page = product_count_last_page or 0  # Если None, установить в 0
        logger.info(f"Количество товароа на странице {product_count}")
        logger.info(f"Количество страниц {pages_count}")
        logger.info(f"Количество товароа на последней странице {product_count_last_page}")
        if pages_count == 1:
            total_product = product_count
            logger.info(f"Всего товаро/услуг {total_product}")
        else:
            total_product = product_count * \
                (pages_count - 1) + product_count_last_page
            logger.info(f"Всего товаро/услуг {total_product}")
        all_data = {
            "total_product":total_product
        }
        return all_data, product_names



def get_last_page(url, last_page, max_retries=10, delay=5):

    retries = 0  # Счётчик попыток

    while retries < max_retries:
        response = requests.get(
            f"{url}product_list/page_{last_page}",
            headers=headers,
            timeout=30,)
        product_count = None
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            content = response.text
            # Парсим HTML с помощью BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            # Количество товаров на странице
            product_count, product_names = get_product_count(soup)
            return product_count
        elif response.status_code == 404:
            return None
        else:
            retries += 1
            logger.error(f"Попытка {retries}/{max_retries}: статус {response.status_code}. Повтор через {delay} секунд...")
            time.sleep(delay)  # Задержка перед повторным запросом
            return product_count



def scrap_contacts(url):
    """
    Извлечение контактной информации с указанной страницы.

    :param url: str - URL страницы с контактной информацией
    :return: dict - Словарь с контактной информацией
    """
    extracted_data = {"contacts": []}
    # Получить содержимое страницы
    content = get_contacts(url)
    if content is None:
        logger.error("Не удалось получить содержимое страницы.")
        return {}

    # Парсим HTML с помощью BeautifulSoup
    soup = BeautifulSoup(content, "lxml")
    # Найти тег <script type="application/ld+json">
    script_tag = soup.find("script", {"type": "application/ld+json"})
    if not script_tag:
        logger.error("Тег <script type='application/ld+json'> не найден.")
        return {}
    logger.info("Найден тег <script type='application/ld+json'>.")

    try:
        # Преобразовать содержимое тега в словарь
        data = json.loads(script_tag.string)
        logger.info("JSON успешно загружен.")

        # Проверка на тип Organization
        if data.get("@type") == "Organization":
            contact_info = {
                "url": data.get("url"),
                "name": data.get("name"),
                "email": data.get("email"),  # Если email есть в JSON
                "telephones": [
                    point.get("telephone")
                    for point in data.get("contactPoint", [])
                    if point.get("telephone")
                ],
                "addressLocality": data.get("address", {}).get("addressLocality"),
                "addressRegion": data.get("address", {}).get("addressRegion"),
                "addressCountryname": data.get("address", {}).get("addressCountry", {}).get("name"),
            }
            # logger.info(contact_info)
            extracted_data["contacts"].append(contact_info)

            return extracted_data
        else:
            logger.error("Данные не содержат тип Organization.")
            return {}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        return {}

def get_contacts(url, headers=None, max_retries=10, delay=5):
    """
    Получение HTML-страницы списка продуктов с обработкой повторных запросов.

    :param url: str - Базовый URL
    :param headers: dict - Заголовки для запроса
    :param max_retries: int - Максимальное количество попыток
    :param delay: int - Задержка между попытками (в секундах)
    :return: str или None - HTML содержимое или None, если не удалось получить данные
    """
    retries = 0  # Счётчик попыток

    while retries < max_retries:
        try:
            response = requests.get(
                f"{url}/contacts",
                headers=headers,
                timeout=30,
            )

            # Проверка кода ответа
            if response.status_code == 200:
                content = response.text
                logger.info(f"Успешный запрос: статус {response.status_code}")
                return content
            elif response.status_code == 404:
                return None
            else:
                retries += 1
                logger.error(f"Попытка {retries}/{max_retries}: статус {response.status_code}. Повтор через {delay} секунд...")
                time.sleep(delay)

        except requests.RequestException as e:
            retries += 1
            logger.error(
                f"Попытка {retries}/{max_retries}. Ошибка: {e}. Повтор через {delay} секунд...")
            time.sleep(delay)

    # Если все попытки исчерпаны
    logger.error(f"Не удалось получить HTML после {max_retries} попыток.")
    return None

def get_pagination_pages_testimonials(html_content):
    """
    Извлекает количество страниц из атрибута data-pagination-pages-count.
    
    :param html_content: str - HTML-контент
    :return: int - Количество страниц или None, если атрибут не найден
    """
    soup = BeautifulSoup(html_content, "lxml")
    
    pagination_div = soup.find('div', {'data-bazooka': 'Paginator'})
    if pagination_div:
        pages_count = int(pagination_div.get('data-pagination-pages-count'))
        if pages_count:
            
            return int(pages_count)  # Преобразуем в число и возвращаем
    
    return None

def get_testimonials(url, max_retries=10, delay=5):
    """
    Получение HTML-страницы списка отзывов с обработкой повторных запросов.
    
    :param url: str - URL страницы отзывов
    :param headers: dict - Заголовки для запроса
    :param max_retries: int - Максимальное количество попыток
    :param delay: int - Задержка между попытками (в секундах)
    :return: str или None - HTML содержимое или None, если не удалось получить данные
    """
    retries = 0
    while retries < max_retries:
        try:
            url = f"{url}testimonials"
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None
            else:
                retries += 1
                time.sleep(delay)
        except requests.RequestException:
            retries += 1
            time.sleep(delay)
    return None

def scrape_reviews(soup):
    """
    Извлекает отзывы за 2023 и 2024 годы с текущей страницы.
    
    :param soup: BeautifulSoup - Объект BeautifulSoup страницы
    :return: list - Список отзывов, bool - Флаг остановки
    """
    reviews = []
    review_items = soup.find_all("li", class_="cs-comments__item")
    # logger.info(f"Найдено отзывов на странице: {len(review_items)}")

    for item in review_items:
        # Извлекаем дату
        date_tag = item.find("time", class_="cs-date")
        review_date = date_tag["datetime"].split("T")[0] if date_tag and date_tag.has_attr("datetime") else None
        # logger.info(f"Дата отзыва: {review_date}")

        if review_date:
            year = int(review_date.split("-")[0])
            # logger.info(f"Год отзыва: {year}")

            # Проверка года
            if year < 2023:
                logger.info("Год меньше 2023, прекращаем сбор.")
                return reviews, True
            elif year > 2024:
                logger.info("Год больше 2024, пропускаем отзыв.")
                continue

        # Извлекаем рейтинг
        rating_tag = item.find("span", class_="cs-rating__state")
        rating_text = rating_tag["title"] if rating_tag and rating_tag.has_attr("title") else None
        # logger.info(f"Текст рейтинга: {rating_text}")

        rating = int(rating_text.split()[1]) if rating_text and "Рейтинг" in rating_text else None
        if rating is None:
            logger.warning("Не удалось извлечь рейтинг, пропускаем отзыв.")
            continue

        # Добавление отзыва
        if review_date and rating is not None:
            reviews.append({"date": review_date, "rating": rating})
            # logger.info(f"Добавлен отзыв: дата={review_date}, рейтинг={rating}")

    logger.info(f"Всего собранных отзывов: {len(reviews)}")
    logger.info(reviews)
    return reviews, False

def parse_reviews(url):
    """
    Парсит отзывы со всех страниц, пока не найдёт отзывы за год раньше 2023.
    
    :param url: str - URL страницы отзывов
    :param headers: dict - Заголовки для запросов
    :return: list - Список всех собранных отзывов
    """
    extracted_data = {"reviews": []}

    # Первая страница
    html_content = get_testimonials(url)
    # #Сохранение контента
    # if html_content:
    #     save_html_to_file(html_content, "testimonials.html")
    # else:
    #     logger.error("Не удалось получить HTML-контент.")
    
    if not html_content:
        return extracted_data

    soup = BeautifulSoup(html_content, "lxml")
    total_pages = get_pagination_pages_testimonials(html_content)
    logger.info(f"Количество страниц {total_pages}")

    # Собираем отзывы с первой страницы
    page_reviews, stop = scrape_reviews(soup)
    # Добавляем отзывы в список
    extracted_data["reviews"].extend(page_reviews)
    # Проверяем, нужно ли продолжать
    if stop or not total_pages:
        return extracted_data

    # Переходим к следующим страницам
    for page in range(2, total_pages + 1):
        next_page_url = f"{url}testimonials/page_{page}"
        html_content = get_testimonials(next_page_url)
        if not html_content:
            break

        soup = BeautifulSoup(html_content, "lxml")
        page_reviews, stop = scrape_reviews(soup)
        # Добавляем отзывы в список
        extracted_data["reviews"].extend(page_reviews)

        if stop:  # Останавливаем, если найден отзыв за год раньше 2023
            break
    return extracted_data
def save_html_to_file(html_content, file_path):
    """
    Сохраняет HTML-контент в файл.
    
    :param html_content: str - HTML-контент для сохранения
    :param file_path: str - Путь к файлу для сохранения
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        logger.info(f"HTML сохранён в файл: {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении HTML: {e}")
def merge_data(reviews, contact_info, total_products, product_names):
    """
    Объединяет данные отзывов, контактной информации и общего количества продуктов в один JSON.

    :param reviews: dict - Словарь с ключом "reviews" и списком отзывов
    :param contact_info: dict - Словарь с ключом "contacts" и списком контактной информации
    :param total_products: dict - Словарь с ключом "total_product" и значением общего количества продуктов
    :return: dict - Объединённый JSON
    """
    combined_data = {}
    
    # Добавляем данные, если они есть
    if reviews and isinstance(reviews, dict):
        combined_data.update(reviews)
    if contact_info and isinstance(contact_info, dict):
        combined_data.update(contact_info)
    if total_products and isinstance(total_products, dict):
        combined_data.update(total_products)
    if product_names and isinstance(product_names, list):
        combined_data["product_names"] = product_names  # Добавляем список товаров
        # Объединяем данные
    # Преобразуем в JSON-строку (опционально)
    return combined_data
def save_to_file_json(data, filename):
    """
    Сохраняет данные в JSON-файл.

    :param data: dict - Данные для записи
    :param filename: str - Имя файла
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info(f"Данные успешно записаны в файл: {filename}")
    except Exception as e:
        logger.error(f"Ошибка при записи в файл: {e}")
def save_to_excel(data, filename):
    """
    Сохраняет данные в Excel-файл с использованием pandas.
    
    :param data: dict - Данные для записи
    :param filename: str - Имя файла
    """
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        # Записываем отзывы
        if "reviews" in data and isinstance(data["reviews"], list):
            reviews_df = pd.DataFrame(data["reviews"])
            reviews_df.to_excel(writer, sheet_name="Reviews", index=False)

        # Записываем контакты
        if "contacts" in data and isinstance(data["contacts"], list):
            contacts_df = pd.DataFrame(data["contacts"])
            contacts_df.to_excel(writer, sheet_name="Contacts", index=False)

        # Записываем общее количество продуктов
        if "total_product" in data:
            total_product_df = pd.DataFrame(
                [{"total_product": data["total_product"]}]
            )
            total_product_df.to_excel(writer, sheet_name="TotalProduct", index=False)

    logger.info(f"Данные успешно записаны в файл: {filename}")

def write_combined_data_to_csv_v2(combined_data, filename="combined_data.csv"):
    """
    Записывает данные в CSV в одну строку, с каждым значением в своей колонке.
    
    :param combined_data: dict - Данные для записи
    :param filename: str - Имя файла CSV
    """
    with open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        
        # Заголовки
        headers = []
        values = []
        
        # Добавляем отзывы
        reviews = combined_data.get("reviews", [])
        for i, review in enumerate(reviews, 1):
            headers.append(f"review_{i}_date")
            values.append(review.get("date", ""))
            headers.append(f"review_{i}_rating")
            values.append(review.get("rating", ""))
        
        # Добавляем контактную информацию
        contacts = combined_data.get("contacts", [])
        if contacts:
            contact = contacts[0]  # Берём первый контакт
            for key, value in contact.items():
                if isinstance(value, list):
                    headers.append(key)
                    values.append(", ".join(value))
                else:
                    headers.append(key)
                    values.append(value)
        
        # Добавляем общее количество продуктов
        headers.append("total_product")
        values.append(combined_data.get("total_product", ""))
        
        # Добавляем названия продуктов
        headers.append("product_names")
        values.append(", ".join(combined_data.get("product_names", [])))
        
        # Пишем в файл
        writer.writerow(headers)
        writer.writerow(values)
    logger.info(f"Данные успешно записаны в {filename}")

def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()

def main():
    url = "https://oil-market.kz/"
    urls = read_cities_from_csv(output_csv_file)
    for url in urls[:10]:
        file_name = url.split("/")[-2].replace("-", "_").replace(".", "_")
        total_products, product_names  = get_total_products(url)
        contact_info = scrap_contacts(url)
        reviews = parse_reviews(url)

        # Объединяем данные
        combined_json = merge_data(reviews, contact_info, total_products, product_names)
            # Сохраняем combined_json в файл
        csv_files = csv_directory / f"{file_name}.csv"
        if csv_files.exists():
            continue
        write_combined_data_to_csv_v2(combined_json, csv_files)
        # save_to_file_json(combined_json, "combined_data.json")
        # # Сохраняем combined_json в Excel
        # save_to_excel(combined_json, "combined_data.xlsx")
if __name__ == "__main__":
    main()
    
