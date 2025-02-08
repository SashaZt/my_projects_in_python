import json
import sys
from pathlib import Path
import pandas as pd
import requests
from loguru import logger
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from pathlib import Path
import time
import requests
from requests.exceptions import RequestException
import json
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
from sqlalchemy.orm import Session
import pandas as pd
from sqlalchemy import select, join
import pandas as pd
import requests
from loguru import logger
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
import time
import json
from pathlib import Path
from datetime import datetime
import logging
from collections import defaultdict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine, String, Integer
import json

current_directory = Path.cwd()
json_category_directory = current_directory / "json_category"
json_comment_directory = current_directory / "json_comment"
log_directory = current_directory / "log"
data_directory = current_directory / "data"
html_directory = current_directory / "html"
html_id_directory = current_directory / "html_id"

html_id_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
json_category_directory.mkdir(parents=True, exist_ok=True)
json_comment_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
output_csv_file = data_directory / "output.csv"
output_id_csv_file = data_directory / "output_id.csv"
output_xlsx_file = data_directory / "output.xlsx"

BASE_URL = "https://kaspi.kz"
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 'Cookie': 'layout=d; dt-i=env=production|ssrVersion=v1.18.39|pageMode=catalog; ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
    "DNT": "1",
    "Pragma": "no-cache",
    "Referer": "https://kaspi.kz/shop/c/categories/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

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
class Base(DeclarativeBase):
    pass

# Определяем модель для таблицы
class Merchant(Base):
    __tablename__ = 'merchants'
    __table_args__ = {'extend_existing': True}  # Добавляем этот параметр
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    create_date = Column(DateTime)
    sales_count = Column(Integer)
    rating = Column(Float)
    
    def __repr__(self):
        return f"<Merchant(uid={self.uid}, name={self.name})>"
class Review(Base):
    __tablename__ = 'reviews'
    __table_args__ = {'extend_existing': True}  # Добавляем этот параметр
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(String(100), nullable=False)
    year_2025: Mapped[int] = mapped_column(Integer, nullable=True)
    year_2024: Mapped[int] = mapped_column(Integer, nullable=True)
    year_2023: Mapped[int] = mapped_column(Integer, nullable=True)
    year_2022: Mapped[int] = mapped_column(Integer, nullable=True)
    year_2021: Mapped[int] = mapped_column(Integer, nullable=True)
    year_2020: Mapped[int] = mapped_column(Integer, nullable=True)
    year_2019: Mapped[int] = mapped_column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Review(uid={self.uid})>"
def create_db_connection(
    user="python_mysql", password="python_mysql", host="localhost", db="kaspi_kz"
):
    """Create database connection and return engine"""
    engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{db}", echo=True)
    return engine

def init_db(engine):
    """Инициализация базы данных"""
    Base.metadata.create_all(engine)

def save_merchant_data(engine, merchant_data):
    """Сохранение данных о продавце в базу данных"""
    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Преобразуем строку даты в объект datetime
        create_date = datetime.strptime(merchant_data['create'], '%Y-%m-%dT%H:%M:%S.%f')
        
        # Создаем новый объект Merchant
        merchant = Merchant(
            uid=merchant_data['uid'],
            name=merchant_data['name'],
            phone=merchant_data['phone'],
            create_date=create_date,
            sales_count=merchant_data['salesCount'],
            rating=merchant_data['rating']
        )
        
        # Проверяем, существует ли уже продавец с таким uid
        existing_merchant = session.query(Merchant).filter_by(uid=merchant_data['uid']).first()
        
        if existing_merchant:
            # Обновляем существующую запись
            existing_merchant.name = merchant.name
            existing_merchant.phone = merchant.phone
            existing_merchant.create_date = merchant.create_date
            existing_merchant.sales_count = merchant.sales_count
            existing_merchant.rating = merchant.rating
        else:
            # Добавляем новую запись
            session.add(merchant)
        
        # Сохраняем изменения
        session.commit()
        print(f"Successfully saved/updated merchant with UID: {merchant_data['uid']}")
        
    except Exception as e:
        print(f"Error saving merchant data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def get_json_category():

    cookies = {
        "ks.tg": "47",
        "k_stat": "a6864b24-87cc-4ce5-94ea-db68e661c075",
        "current-action-name": "Index",
        "kaspi.storefront.cookie.city": "750000000",
    }

    headers = {
        "Accept": "application/json, text/*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        # 'Cookie': 'ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
        "DNT": "1",
        "Referer": "https://kaspi.kz/shop/c/categories/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "X-KS-City": "750000000",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    codes = [
        "Smartphones and gadgets",
        "Home equipment",
        "TV_Audio",
        "Computers",
        "Furniture",
        "Beauty care",
        "Child goods",
        "Pharmacy",
        "Construction and repair",
        "Sports and outdoors",
        "Leisure",
        "Car goods",
        "Jewelry and Bijouterie",
        "Fashion accessories",
        "Fashion",
        "Shoes",
        "Pet goods",
        "Home",
        "Gifts and party supplies",
        "Office and school supplies",
    ]
    for code in codes:
        logger.info(code)
        params = {
            "depth": "2",
            "city": "750000000",
            "code": code,
            "rootType": "desktop",
        }
        json_category_file = json_category_directory / f"{code}.json"
        if json_category_file.exists():
            continue
        response = requests.get(
            "https://kaspi.kz/yml/main-navigation/n/n/desktop-menu",
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )

        # Проверка успешности запроса
        if response.status_code == 200:
            json_data = response.json()
            with open(json_category_file, "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
            logger.info(json_category_file)
        else:
            logger.error(response.status_code)


def scrap_json_category():
    all_data = []
    for json_file in json_category_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        subnodes_level_01 = data.get("subNodes", None)
        if subnodes_level_01:
            for level_02 in subnodes_level_01:
                subnodes_level_02 = level_02.get("subNodes", None)
                if subnodes_level_02:
                    for level_03 in subnodes_level_02:
                        subnodes_level_03 = level_03.get("link", None)
                        url = f"{BASE_URL}{subnodes_level_03}"
                        all_data.append(url)

    # Создать DataFrame из списка URL
    df = pd.DataFrame(all_data, columns=["url"])

    # Записать DataFrame в CSV файл
    df.to_csv(output_csv_file, index=False)


def main_th():
    urls = []
    with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for url in urls:
            output_html_file = (
                html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
            )

            if not os.path.exists(output_html_file):
                futures.append(executor.submit(get_html, url, output_html_file))
            else:
                print(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def fetch(url):
    cookies = {
        "layout": "d",
        "dt-i": "env=production|ssrVersion=v1.18.39|pageMode=catalog",
        "ks.tg": "47",
        "k_stat": "a6864b24-87cc-4ce5-94ea-db68e661c075",
        "current-action-name": "Index",
        "kaspi.storefront.cookie.city": "750000000",
    }

    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logger.error(f"An error occurred: {err}")
        return None
    return response.text


def get_html(url, html_file):
    src = fetch(url)
    if src:
        with open(html_file, "w", encoding="utf-8") as file:
            file.write(src)
        logger.info(f"HTML saved to {html_file}")


def main_th_id():
    ids = []
    with open(output_id_csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ids.append(row["url"])

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for id_site in ids:
            output_html_file = (
                html_id_directory
                / f"html_{hashlib.md5(id_site.encode()).hexdigest()}.html"
            )

            if not os.path.exists(output_html_file):
                futures.append(executor.submit(get_html_id, id_site, output_html_file))
            else:
                logger.warning(f"Файл для {id} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def fetch_id(merchantId):
    cookies = {
        "layout": "d",
        "dt-i": "env=production|ssrVersion=v1.18.39|pageMode=merchant",
        "ks.tg": "47",
        "k_stat": "a6864b24-87cc-4ce5-94ea-db68e661c075",
        "current-action-name": "Index",
        "kaspi.storefront.cookie.city": "750000000",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'layout=d; dt-i=env=production|ssrVersion=v1.18.39|pageMode=merchant; ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    try:
        url = f"https://kaspi.kz/shop/info/merchant/{merchantId}/address-tab/"
        logger.info(url)
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(response.status_code)
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logger.error(f"An error occurred: {err}")
        return None
    return response.text


def get_html_id(url, html_file):
    src = fetch_id(url)
    if src:
        with open(html_file, "w", encoding="utf-8") as file:
            file.write(src)
        logger.info(f"HTML saved to {html_file}")


def scrap_html():
    all_data = set()
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Используем регулярное выражение для поиска данных allMerchants
        pattern = re.compile(r'\{"id":"(:allMerchants:[^"]+)",.*?\}', re.DOTALL)
        matches = pattern.findall(content)

        # Создаем список словарей с найденными данными
        all_merchants = []
        for match in matches:
            merchant_pattern = re.compile(
                r'\{"id":"' + re.escape(match) + r'",.*?\}', re.DOTALL
            )
            merchant_data = merchant_pattern.search(content)
            if merchant_data:
                all_merchants.append(json.loads(merchant_data.group(0)))

        # Выводим результаты
        for merchant in all_merchants:
            id_site = merchant["id"].replace(":allMerchants:", "")
            all_data.add(id_site)
        # Создать DataFrame из списка URL
    df = pd.DataFrame(all_data, columns=["url"])

    # Записать DataFrame в CSV файл
    df.to_csv(output_id_csv_file, index=False)
def scrap_html_id():
    engine = create_db_connection()
    init_db(engine)
    
    all_data = []
    for html_file in html_id_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        pattern = r'BACKEND\.components\.merchant = ({.*?});?\s*</script>'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            json_str = match.group(1).strip()
            try:
                merchant_data = json.loads(json_str)
                data = {
                    "uid": merchant_data.get("uid"),
                    "name": merchant_data.get("name"),
                    "phone": merchant_data.get("phone"),
                    "create": merchant_data.get("create"),
                    "salesCount": merchant_data.get("salesCount"),
                    "rating": merchant_data.get("rating")
                }
                # Сохраняем данные в БД
                save_merchant_data(engine, data)
                
                all_data.append(data)
                logger.info(data)
            except Exception as e:
                logger.error(f"Error processing merchant data: {e}")
                
    return all_data

def get_json_comment(merchant):

    cookies = {
        'ks.tg': '47',
        'k_stat': 'a6864b24-87cc-4ce5-94ea-db68e661c075',
        'current-action-name': 'Index',
        'kaspi.storefront.cookie.city': '750000000',
    }

    headers = {
        'Accept': 'application/json, text/*',
        'Accept-Language': 'ru,en;q=0.9,uk;q=0.8',
        'Connection': 'keep-alive',
        # 'Cookie': 'ks.tg=47; k_stat=a6864b24-87cc-4ce5-94ea-db68e661c075; current-action-name=Index; kaspi.storefront.cookie.city=750000000',
        'DNT': '1',
        'Referer': 'https://kaspi.kz/shop/info/merchant/1274021/address-tab/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'X-KS-City': '750000000',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    try:
        for page in range(0, 3):
            json_file_path = json_comment_directory / f"0{page}_{merchant}.json"
            
            # Пропускаем существующие файлы
            if json_file_path.exists():
                logger.info(f"File already exists: {json_file_path}")
                continue
                
            params = {
                'limit': '1000',
                'page': page,
                'filter': 'COMMENT',
                'sort': 'DATE',
                'withAgg': 'false',
                'days': '2000',
            }
            
            try:
                response = requests.get(
                    f'https://kaspi.kz/yml/review-view/api/v1/reviews/merchant/{merchant}',
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()  # Проверяем статус ответа
                
                # Сохраняем JSON
                with open(json_file_path, "w", encoding="utf-8") as json_file:
                    json.dump(response.json(), json_file, ensure_ascii=False, indent=4)
                
                logger.info(f"Successfully saved {json_file_path}")
                
                # Добавляем небольшую задержку между запросами
                time.sleep(1)
                
            except RequestException as e:
                logger.error(f"Error fetching data for merchant {merchant}, page {page}: {e}")
                continue
                
        return f"Completed processing merchant {merchant}"
        
    except Exception as e:
        logger.error(f"Unexpected error processing merchant {merchant}: {e}")
        return f"Failed processing merchant {merchant}: {str(e)}"
        
def main_comment():
    # Читаем IDs из CSV
    ids = []
    try:
        with open(output_id_csv_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            ids = [row["url"] for row in reader]
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return

    # Запускаем обработку в пуле потоков
    with ThreadPoolExecutor(max_workers=50) as executor:
        # Создаем словарь для отслеживания задач
        future_to_merchant = {executor.submit(get_json_comment, merchant): merchant for merchant in ids}
        
        # Обрабатываем результаты по мере их завершения
        for future in as_completed(future_to_merchant):
            merchant = future_to_merchant[future]
            try:
                result = future.result()
                logger.info(result)
            except Exception as e:
                logger.error(f"Error processing merchant {merchant}: {e}")
def process_reviews_by_year():
    all_stats = []
    # Группируем файлы по merchant_uid
    merchant_files = {}
    
    try:
        # Получаем все JSON файлы
        json_files = list(Path(json_comment_directory).glob("[0-9]*_*.json"))
        
        # Группируем файлы по merchant_uid
        for json_file in json_files:
            merchant_uid = json_file.stem.split('_')[1]
            if merchant_uid not in merchant_files:
                merchant_files[merchant_uid] = []
            merchant_files[merchant_uid].append(json_file)
        
        # Обрабатываем файлы каждого мерчанта
        for merchant_uid, files in merchant_files.items():
            stats = defaultdict(int)
            
            for json_file in files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Обрабатываем каждый отзыв
                    for review in data.get('data', []):
                        try:
                            date_str = review.get('date')
                            if date_str:
                                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                                year = date_obj.year
                                stats[str(year)] += 1
                        except ValueError as e:
                            logger.error(f"Error parsing date in review: {date_str}, Error: {e}")
                            continue
                            
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON file {json_file}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing file {json_file}: {e}")
                    continue
            
            # Формируем результат для текущего мерчанта
            result = {
                "uid": merchant_uid
            }
            # Добавляем статистику по годам в порядке убывания
            for year in sorted(stats.keys(), reverse=True):
                result[year] = str(stats[year])
            
            all_stats.append(result)
            logger.info(f"Processed merchant: {merchant_uid}")
        
        return all_stats
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

def save_stats_to_json(stats, output_file):
    if stats:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            logger.info(f"Statistics saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving statistics to file: {e}")
def import_reviews_from_json(json_file):
    engine = create_db_connection()
    init_db(engine)
    """Импорт данных из JSON файла в базу данных"""
    from sqlalchemy.orm import Session
    
    # Читаем JSON файл
    with open(json_file, 'r', encoding='utf-8') as f:
        reviews_data = json.load(f)
    
    # Создаем сессию
    session = Session(engine)
    
    try:
        for review_data in reviews_data:
            # Создаем объект Review
            review = Review(
                uid=review_data['uid'],
                year_2025=int(review_data.get('2025', 0)),
                year_2024=int(review_data.get('2024', 0)),
                year_2023=int(review_data.get('2023', 0)),
                year_2022=int(review_data.get('2022', 0)),
                year_2021=int(review_data.get('2021', 0)),
                year_2020=int(review_data.get('2020', 0)),
                year_2019=int(review_data.get('2019', 0))
            )
            
            # Проверяем существование записи
            existing_review = session.query(Review).filter_by(uid=review.uid).first()
            
            if existing_review:
                # Обновляем существующую запись
                existing_review.year_2025 = review.year_2025
                existing_review.year_2024 = review.year_2024
                existing_review.year_2023 = review.year_2023
                existing_review.year_2022 = review.year_2022
                existing_review.year_2021 = review.year_2021
                existing_review.year_2020 = review.year_2020
                existing_review.year_2019 = review.year_2019
            else:
                # Добавляем новую запись
                session.add(review)
            
        # Сохраняем изменения
        session.commit()
        print("Data successfully imported")
        
    except Exception as e:
        print(f"Error importing data: {e}")
        session.rollback()
    finally:
        session.close()
def export_to_excel(engine, output_file='merchants_reviews.xlsx'):
    try:
        # Создаем запрос для объединения таблиц
        query = select(
            Merchant.uid,
            Merchant.name,
            Merchant.phone,
            Merchant.create_date,
            Merchant.sales_count,
            Merchant.rating,
            Review.year_2025,
            Review.year_2024,
            Review.year_2023,
            Review.year_2022,
            Review.year_2021,
            Review.year_2020,
            Review.year_2019
        ).join(Review, Merchant.uid == Review.uid)

        # Выполняем запрос и получаем данные
        with Session(engine) as session:
            results = session.execute(query).all()

        # Преобразуем результаты в DataFrame
        df = pd.DataFrame(results, columns=[
            'UID', 'Название', 'Телефон', 'Дата создания', 
            'Количество продаж', 'Рейтинг',
            'Отзывы 2025', 'Отзывы 2024', 'Отзывы 2023',
            'Отзывы 2022', 'Отзывы 2021', 'Отзывы 2020', 'Отзывы 2019'
        ])

        # Форматируем дату
        df['Дата создания'] = pd.to_datetime(df['Дата создания']).dt.strftime('%d.%m.%Y')

        # Создаем writer для Excel с engine='xlsxwriter'
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Записываем DataFrame в Excel
            df.to_excel(writer, sheet_name='Статистика', index=False)

            # Получаем объект workbook и worksheet
            workbook = writer.book
            worksheet = writer.sheets['Статистика']

            # Форматирование
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'align': 'center',
                'border': 1,
                'bg_color': '#D9E1F2'
            })

            # Устанавливаем ширину столбцов
            worksheet.set_column('A:A', 15)  # UID
            worksheet.set_column('B:B', 30)  # Название
            worksheet.set_column('C:C', 15)  # Телефон
            worksheet.set_column('D:D', 15)  # Дата создания
            worksheet.set_column('E:E', 15)  # Количество продаж
            worksheet.set_column('F:F', 10)  # Рейтинг
            worksheet.set_column('G:M', 12)  # Отзывы по годам

            # Применяем форматирование к заголовкам
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

        logger.info(f"Данные успешно экспортированы в {output_file}")
        print(f"Файл успешно создан: {output_file}")
        
        return True

    except Exception as e:
        logger.error(f"Ошибка при экспорте данных: {e}")
        print(f"Ошибка при создании файла: {e}")
        return False
    
if __name__ == "__main__":
    # Скачиваем все категории
    # get_json_category()
    # Получаем ссылки на все категории 3 уровня
    # scrap_json_category()
    # main_th()
    # scrap_html()
    # main_th_id()
    # scrap_html_id()
    # main_comment()
    # stats = process_reviews_by_year()
    # if stats:
    #     output_file = "merchants_reviews_stats.json"
    #     save_stats_to_json(stats, output_file)
    #     print(f"Processed {len(stats)} merchants")
    #     # Выводим пример первых нескольких записей
    #     print("\nExample of first few records:")
    #     print(json.dumps(stats[:3], indent=2))
    # json_file = "merchants_reviews_stats.json"
    # import_reviews_from_json(json_file)
    # Создаем подключение к БД
    engine = create_db_connection()
    
    # Экспортируем данные
    export_to_excel(engine, 'merchants_reviews_export.xlsx')