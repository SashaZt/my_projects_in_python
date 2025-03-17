import xml.etree.ElementTree as ET
from pathlib import Path
from loguru import logger
import requests
import sys
import re
from bs4 import BeautifulSoup

current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
html_directory = current_directory / "html"
log_directory = current_directory / "log"

html_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

output_xml_file = data_directory / "output.xml"
output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"
log_file_path = log_directory / "log_message.log"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def create_authenticated_session():
    session = requests.Session()

    # Устанавливаем точно те же куки, что и в curl запросе
    initial_cookies = {
        "PHPSESSID": "vl0bn2tq39gg5r0b0u1outhu10",  # Используем PHPSESSID из curl запроса
        "tow_list_style": "Z",
        "last_viewed": "DNXGGHIOERMLNM%5EDNXGGKKOGRMMIM%5EDNXGHHPMKRMMMO",
        "lng": "ua",
    }

    # Применяем куки к сессии
    for key, value in initial_cookies.items():
        session.cookies.set(
            key, value, domain="b2b.batna24.com"
        )  # Обратите внимание на домен

    login_url = "https://b2b.batna24.com/index.php"

    params = {
        "action": "login",
    }

    data = {
        "user_name": "hdsport2006@gmail.com",
        "password": "Hodor15987532",
    }

    login_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://b2b.batna24.com",
        "Referer": "https://b2b.batna24.com/",  # Обновил referer
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        # Добавляем заголовки из curl запроса
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    try:
        logger.info("Попытка авторизации...")
        response = session.post(
            login_url, params=params, headers=login_headers, data=data, timeout=30
        )

        # Проверка статуса ответа
        if response.status_code != 200:
            logger.error(f"Ошибка авторизации, статус: {response.status_code}")
            return None

        # Сохраним куки для отладки
        logger.info(f"Куки после авторизации: {dict(session.cookies)}")

        # Дополнительная проверка успешности авторизации
        if "Вход в систему" in response.text or "login failed" in response.text.lower():
            logger.error("Авторизация не удалась: неверные учетные данные")
            return None

        logger.info("Авторизация успешна")
        return session

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при авторизации: {str(e)}")
        return None


def get_html(url, params=None):
    # Используем такие же заголовки, как в вашем curl-запросе
    protected_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "DNT": "1",
        "Referer": "https://b2b.batna24.com/?op=produkty",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    
    session = create_authenticated_session()

    if session is None:
        logger.error("Failed to create an authenticated session")
        return None, None

    try:
        logger.info(f"Отправка запроса на URL: {url}")
        response = session.get(url, headers=protected_headers, params=params, timeout=30)
        src = response.text
        
        # Проверка кода ответа
        if response.status_code == 200:
            logger.info(f"Успешный ответ со статусом: {response.status_code}")
            soup = get_soup(src)
            
            # Сохранение HTML-страницы
            output_html_file = html_directory / "output.html"
            with open(output_html_file, "w", encoding="utf-8") as file:
                file.write(src)
            logger.info(f"Successfully saved {output_html_file}")
            
            return src, soup
        else:
            logger.error(f"Failed to get HTML. Status code: {response.status_code}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении HTML: {str(e)}")
        return None, None


def get_soup(html_content):
    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(html_content, "lxml")
    return soup


def sum_product_counters(soup):
    """
    Находит элемент категорий в супе и суммирует значения всех счетчиков.

    Args:
        soup (BeautifulSoup): Объект BeautifulSoup с HTML страницей

    Returns:
        int: Сумма всех значений счетчиков
    """
    # Находим div с категориями
    categories_div = soup.find("div", id="tow_list_filters_box_categories")

    if not categories_div:
        return 0

    # Находим все элементы с классом counter
    counter_elements = categories_div.find_all("div", class_="counter")

    total = 0

    # Проходим по всем найденным счетчикам
    for counter in counter_elements:
        # Получаем текст внутри счетчика
        counter_text = counter.text.strip()

        # Удаляем скобки и преобразуем в целое число
        counter_value = re.sub(r"[\(\)]", "", counter_text)

        try:
            total += int(counter_value)
        except ValueError:
            # Если не удалось преобразовать в число, пропускаем
            continue

    return total

def get_total_products():
    url = "https://b2b.batna24.com/?op=produkty&id_grg=DNXJISPJE&grg_name=%D0%9F%D1%80%D0%BE%D0%B4%D1%83%D0%BA%D1%82%D0%B8&id_gre=DNXAESONI"
    
    html_content, soup = get_html(url)
    
    if soup is not None:
        # Получаем сумму всех счетчиков
        total_products = sum_product_counters(soup)
        logger.info(f"Общее количество товаров: {total_products}")
        return total_products
    else:
        logger.error("Не удалось получить HTML или создать soup")
        return 0

if __name__ == "__main__":
    get_total_products()
