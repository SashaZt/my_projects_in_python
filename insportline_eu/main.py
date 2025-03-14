import html
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import gspread
import requests
from config.logger import logger
from oauth2client.service_account import ServiceAccountCredentials

current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
output_xml_file = data_directory / "output.xml"
output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"

cookies = {
    "PHPSESSID": "34p6gltkfskqsq7g1nacpf4ele",
    "cookieconsent": '{"g":{"personal":true,"statistics":true,"marketing":true},"v":1,"s":1}',
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "max-age=0",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}


def get_config():
    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


config = get_config()
SPREADSHEET = config["google"]["spreadsheet"]
SHEET = config["google"]["sheet"]
EMAIL = config["email"]
PASSWORD = config["password"]


def get_google_sheet():
    """Подключается к Google Sheets и возвращает указанный лист."""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            service_account_file, scope
        )
        client = gspread.authorize(creds)

        # Открываем таблицу по ключу и возвращаем лист
        spreadsheet = client.open_by_key(SPREADSHEET)
        logger.info("Успешное подключение к Google Spreadsheet.")
        return spreadsheet.worksheet(SHEET)
    except FileNotFoundError:
        raise FileNotFoundError("Файл credentials.json не найден. Проверьте путь.")
    except gspread.exceptions.APIError as e:
        logger.error(f"Ошибка API Google Sheets: {e}")
        raise
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        raise


# Получение листа Google Sheets
sheet = get_google_sheet()


# def download_xml():

#     response = requests.get(
#         "https://www.insportline.eu/sitemap.xml",
#         cookies=cookies,
#         headers=headers,
#         timeout=30,
#     )

#     # Проверка успешности запроса
#     if response.status_code == 200:
#         # Сохранение содержимого в файл
#         with open(output_xml_file, "wb") as file:
#             file.write(response.content)
#         logger.info(f"Файл успешно сохранен в: {output_xml_file}")
#     else:
#         logger.error(f"Ошибка при скачивании файла: {response.status_code}")


# def parse_sitemap():
#     if os.path.exists(html_directory):
#         shutil.rmtree(html_directory)
#     download_xml()
#     try:
#         # Чтение XML файла
#         with open(output_xml_file, "r", encoding="utf-8") as file:
#             xml_content = file.read()

#         # Парсинг XML
#         root = ET.fromstring(xml_content)

#         # Указание правильного пространства имен
#         namespace = {"ns": "http://www.google.com/schemas/sitemap/0.84"}

#         # Шаблон для фильтрации URL'ов: https://www.insportline.eu/число/что-угодно
#         pattern = r"^https://www\.insportline\.eu/\d+/.*$"

#         # Извлечение URL, соответствующих шаблону
#         urls = []
#         for url_elem in root.findall(".//ns:url", namespace):
#             loc_elem = url_elem.find("ns:loc", namespace)
#             if loc_elem is not None and loc_elem.text:
#                 url = loc_elem.text.strip()
#                 if re.match(pattern, url):
#                     urls.append(url)

#         # Вывод количества найденных URL
#         logger.info(f"Найдено {len(urls)} URL, соответствующих шаблону")

#         # Сохранение в CSV
#         url_data = pd.DataFrame(urls, columns=["url"])
#         url_data.to_csv(output_csv_file, index=False)
#         logger.info(f"URL адреса сохранены в {output_csv_file}")

#         return urls

#     except FileNotFoundError:
#         logger.error(f"Ошибка: Файл {output_xml_file} не найден")
#         return []
#     except ET.ParseError as e:
#         logger.error(f"Ошибка при парсинге XML: {e}")
#         return []
#     except Exception as e:
#         logger.error(f"Произошла ошибка: {e}")
#         return []


# def create_authenticated_session(email, password):
#     """
#     Создает авторизованную сессию для работы с сайтом.

#     Args:
#         email (str): Email для авторизации
#         password (str): Пароль для авторизации

#     Returns:
#         requests.Session or None: Авторизованная сессия или None в случае ошибки
#     """
#     session = requests.Session()
#     # Устанавливаем начальные куки, которые должны быть до авторизации
#     initial_cookies = {
#         "cookieconsent": '{"g":{"personal":true,"statistics":true,"marketing":true},"v":1,"s":1}'
#     }

#     # Применяем куки к сессии
#     for key, value in initial_cookies.items():
#         session.cookies.set(key, value, domain="www.insportline.eu")
#     login_url = "https://www.insportline.eu/scripts/login.php"
#     login_payload = {"customer_email": email, "customer_password": password}
#     login_headers = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#         "accept-language": "ru,en;q=0.9,uk;q=0.8",
#         "content-type": "application/x-www-form-urlencoded",
#         "origin": "https://www.insportline.eu",
#         "referer": "https://www.insportline.eu/login",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
#     }

#     try:
#         response = session.post(
#             login_url, data=login_payload, headers=login_headers, timeout=30
#         )

#         # Проверка статуса ответа
#         if response.status_code != 200:
#             logger.error(f"Ошибка авторизации, статус: {response.status_code}")
#             return None

#         # Дополнительная проверка успешности авторизации
#         # Здесь можно добавить проверку содержимого страницы, например,
#         # поиск определенного элемента, который появляется только после успешного логина
#         if "Вход в систему" in response.text or "login failed" in response.text.lower():
#             logger.error("Авторизация не удалась: неверные учетные данные")
#             return None

#         logger.info("Авторизация успешна")
#         return session

#     except requests.exceptions.RequestException as e:
#         logger.error(f"Ошибка при авторизации: {str(e)}")
#         return None


# def main_th():
#     if not os.path.exists(html_directory):
#         html_directory.mkdir(parents=True, exist_ok=True)
#     urls = []
#     with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             urls.append(row["url"])
#     # Создаем сессию
#     # Создаем авторизованную сессию
#     session = create_authenticated_session(EMAIL, PASSWORD)
#     if session is None:
#         logger.error("Не удалось создать авторизованную сессию. Прерываем выполнение.")
#         return

#     with ThreadPoolExecutor(max_workers=1) as executor:
#         futures = []
#         for url in urls:
#             output_html_file = (
#                 html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
#             )

#             if not os.path.exists(output_html_file):
#                 futures.append(
#                     executor.submit(get_html, url, output_html_file, session)
#                 )
#             else:
#                 logger.info(f"Файл для {url} уже существует, пропускаем.")

#         results = []
#         for future in as_completed(futures):
#             # Здесь вы можете обрабатывать результаты по мере их завершения
#             results.append(future.result())


# def fetch(url, session):
#     protected_headers = {
#         "referer": "https://www.insportline.eu/login",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
#     }

#     # Проверяем, есть ли в сессии нужные куки
#     if "PHPSESSID" not in session.cookies:
#         logger.warning(
#             "Сессия не содержит нужных куки (PHPSESSID). Возможно, авторизация не работает."
#         )

#     try:
#         logger.debug(f"Запрос к {url} с куками: {dict(session.cookies)}")
#         response = session.get(url, headers=protected_headers, timeout=30)

#         # Проверяем, не произошло ли перенаправление на страницу логина
#         if "login" in response.url.lower() and "login" not in url.lower():
#             logger.warning(
#                 f"Произошло перенаправление на страницу логина. Сессия, возможно, недействительна."
#             )
#             return None

#         # Проверка статуса ответа
#         if response.status_code != 200:
#             logger.warning(
#                 f"Статус не 200 для {url}. Получен статус: {response.status_code}. Пропускаем."
#             )
#             return None

#         # Проверка на наличие признаков авторизованного пользователя в ответе
#         # Это зависит от конкретного сайта - нужно найти элемент, который виден только авторизованным пользователям
#         # Например, ссылка на личный кабинет, имя пользователя и т.п.
#         if "login" in response.text.lower() and "logout" not in response.text.lower():
#             logger.warning(
#                 "В ответе есть форма логина, но нет кнопки выхода. Возможно, сессия недействительна."
#             )

#         if "logout" in response.text.lower() or "account" in response.text.lower():
#             logger.debug("Обнаружены признаки авторизованного пользователя в ответе.")

#         return response.text

#     except requests.exceptions.RequestException as e:
#         logger.error(f"Ошибка при загрузке {url}: {str(e)}")
#         return None


# def get_html(url, html_file, session):
#     src = fetch(url, session)

#     if src is None:
#         return url, html_file, False

#     with open(html_file, "w", encoding="utf-8") as file:
#         file.write(src)

#     logger.info(f"Успешно загружен и сохранен: {html_file}")
#     return url, html_file, True


def ensure_row_limit(sheet, required_rows=10000):
    """Увеличивает количество строк в листе Google Sheets, если их меньше требуемого количества."""
    current_rows = len(sheet.get_all_values())
    if current_rows < required_rows:
        sheet.add_rows(required_rows - current_rows)


# def pars_htmls():
#     logger.info("Собираем данные со страниц html")
#     all_data = []

#     # Пройтись по каждому HTML файлу в папке
#     for html_file in html_directory.glob("*.html"):
#         with html_file.open(encoding="utf-8") as file:
#             content = file.read()

#         # Парсим HTML с помощью BeautifulSoup
#         soup = BeautifulSoup(content, "lxml")
#         # Поиск скрипта с типом application/ld+json и типом Product
#         product_script = soup.find(
#             "script",
#             type="application/ld+json",
#             string=lambda text: text and '"@type": "Product"' in text,
#         )

#         if product_script:
#             try:
#                 product_data = json.loads(product_script.string)
#                 # Извлекаем имя продукта из корневого объекта
#                 product_name = product_data.get("name")
#                 sku = product_data.get("mpn")

#                 # Извлекаем данные из offers
#                 offers = product_data.get("offers", {})
#                 offer_price = offers.get("price")
#                 if offer_price:
#                     offer_price = str(offer_price).replace(".", ",")
#                 availability = offers.get("availability")
# all_availability = {
#     "PreOrder": "Попереднє замовлення",
#     "InStock": "В наявності",
#     "OutOfStock": "Немає в наявності",
# }
#                 result_availability = None  # По умолчанию None, если ничего не найдено
#                 for term in all_availability:
#                     if availability and term in availability:
#                         result_availability = all_availability[term]
#                         break

# data_json = {
#     "Назва": product_name,
#     "Код товару (INS)": f"INS{sku}",
#     "Ціна": offer_price,
#     "Наявність": result_availability,
# }
#                 all_data.append(data_json)

#             except json.JSONDecodeError as e:
#                 logger.error(f"Ошибка парсинга JSON: {e}")
#                 # Или можно использовать print:
#                 logger.info(f"Ошибка парсинга JSON: {e}")
#         else:
#             logger.error("Product JSON не найден.")
#             # Или можно использовать print:
#             logger.info("Product JSON не найден.")

#     update_sheet_with_data(sheet, all_data)


# ensure_row_limit(sheet, 1000)


def update_sheet_with_data(sheet, data, total_rows=10000):
    """Записывает данные в указанные столбцы листа Google Sheets с использованием пакетного обновления."""
    if not data:
        raise ValueError("Данные для обновления отсутствуют.")

    # Заголовки из ключей словаря
    headers = list(data[0].keys())

    # Запись заголовков в первую строку
    sheet.update(values=[headers], range_name="A1", value_input_option="RAW")

    # Формирование строк для записи
    rows = [[entry.get(header, "") for header in headers] for entry in data]

    # Добавление пустых строк до общего количества total_rows
    if len(rows) < total_rows:
        empty_row = [""] * len(headers)
        rows.extend([empty_row] * (total_rows - len(rows)))

    # Определение диапазона для записи данных
    end_col = chr(65 + len(headers) - 1)  # Преобразование индекса в букву (A, B, C...)
    range_name = f"A2:{end_col}{total_rows + 1}"

    # Запись данных в лист
    sheet.update(values=rows, range_name=range_name, value_input_option="USER_ENTERED")


def download_xml():
    if os.path.exists(html_directory):
        shutil.rmtree(html_directory)
    cookies = {
        "PHPSESSID": "34p6gltkfskqsq7g1nacpf4ele",
        "cookieconsent": '{"g":{"personal":true,"statistics":true,"marketing":true},"v":1,"s":1}',
        "customer_session_hash": "2252690%3Ab5b7716efc8052c98dfb7288afbb1024",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        # 'cookie': 'PHPSESSID=34p6gltkfskqsq7g1nacpf4ele; cookieconsent={"g":{"personal":true,"statistics":true,"marketing":true},"v":1,"s":1}; customer_session_hash=2252690%3Ab5b7716efc8052c98dfb7288afbb1024',
    }

    params = {
        "hash": "mvthrjgcg5",
    }

    response = requests.get(
        "https://www.insportline.eu/xml_feed_vse2.php",
        params=params,
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(output_xml_file, "wb") as file:
            file.write(response.content)
        logger.info(f"Файл успешно сохранен в: {output_xml_file}")
    else:
        logger.error(f"Ошибка при скачивании файла: {response.status_code}")


def clean_text(text):
    """
    Очищает текст от HTML-сущностей, экранированных символов и других проблемных символов

    Args:
        text (str): Исходный текст

    Returns:
        str: Очищенный текст
    """
    if text is None:
        return ""

    # Декодируем HTML-сущности (включая &quot;)
    text = html.unescape(text)

    # Заменяем экранированные кавычки и другие специальные символы
    replacements = [
        ('\\\\"', '"'),  # Двойное экранирование: \\\"
        ('\\"', '"'),  # Экранированная двойная кавычка: \"
        ('"', '"'),  # Альтернативная запись: \"
        ("\\'", "'"),  # Экранированная одинарная кавычка: \'
        ("\\\\", "\\"),  # Экранированный обратный слеш: \\
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    # Удаляем управляющие символы
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)

    return text


def parse_shop_xml():
    """
    Парсит XML-файл магазина и возвращает список словарей с выбранными данными продуктов.

    Возвращает:
        Список словарей с пользовательскими полями
    """
    try:
        # Словарь соответствия значений наличия
        all_availability = {
            "1": "В наявності",
            "0": "Немає в наявності",
        }

        # Парсим XML-файл
        tree = ET.parse(output_xml_file)
        root = tree.getroot()

        # Список для хранения продуктов
        products = []

        # Общее количество обработанных элементов
        total_items = 0

        # Обработка каждого SHOPITEM
        for shopitem in root.findall("SHOPITEM"):
            total_items += 1

            # Извлекаем необходимые поля
            product_element = shopitem.find("PRODUCT")
            productno_element = shopitem.find("PRODUCTNO")
            price_element = shopitem.find("PURCHASE_PRICE")
            instock_element = shopitem.find("IN_STOCK")

            product = (
                product_element.text.replace('"', "")
                if product_element is not None and product_element.text
                else None
            )
            productno = (
                productno_element.text
                if productno_element is not None and productno_element.text
                else None
            )
            price = (
                price_element.text.replace(".", ",")
                if price_element is not None and price_element.text
                else None
            )
            instock = (
                instock_element.text
                if instock_element is not None and instock_element.text
                else None
            )

            # Преобразуем значение наличия
            availability = all_availability.get(instock, instock)

            # Создаем словарь с нашими собственными ключами
            data_json = {
                "Назва": product,
                "Код товару (INS)": f"INS{productno}",
                "Ціна": price,
                "Наявність": availability,
            }
            # Добавляем продукт в список
            products.append(data_json)

        # Сохраняем в JSON-файл
        with open(output_json_file, "w", encoding="utf-8") as json_file:
            json.dump(products, json_file, ensure_ascii=False, indent=4)
        update_sheet_with_data(sheet, products)
        logger.info(
            f"Обработано {total_items} товаров, сохранено {len(products)} товаров"
        )
        return products

    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return []


if __name__ == "__main__":
    # parse_sitemap()
    # main_th()
    # pars_htmls()
    download_xml()
    parse_shop_xml()
