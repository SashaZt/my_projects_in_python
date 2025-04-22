import asyncio
import csv
import json
import os
import random
import re
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import gspread
import pandas as pd
import requests
from bs4 import BeautifulSoup
from config.logger import logger
from oauth2client.service_account import ServiceAccountCredentials
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.axis import ChartLines

# Настройка путей
current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
html_directory = current_directory / "html"

# Создание директорий, если они не существуют
for directory in [html_directory, config_directory, data_directory]:
    directory.mkdir(parents=True, exist_ok=True)

# Определение путей к файлам
output_xml_file = data_directory / "output.xml"
output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"


def get_config() -> dict:
    """
    Загружает конфигурацию из JSON-файла.
    
    Returns:
        dict: Данные конфигурации.
    """
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        logger.error(f"Файл конфигурации не найден: {config_file}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON в файле: {config_file}")
        raise


# Загрузка конфигурации
try:
    config = get_config()
    SPREADSHEET = config["google"]["spreadsheet"]
    SHEET = config["google"]["sheet"]
    CONTRACTOR_CODE = config["site"]["contractor_code"]
    NAME = config["site"]["name"]
    PASSWORD = config["site"]["password"]
except (KeyError, FileNotFoundError, json.JSONDecodeError) as e:
    logger.critical(f"Ошибка при загрузке конфигурации: {e}")
    raise


def get_session() -> Optional[requests.Session]:
    """
    Авторизуется на сайте и возвращает активную сессию.
    
    Returns:
        Optional[requests.Session]: Сессия с авторизацией или None в случае ошибки.
    """
    try:
        # Создаем сессию
        session = requests.Session()
        
        # Делаем POST запрос для авторизации
        login_url = "https://panel.bachasport.pl/login"
        login_payload = {
            "_token": "OTVStyCnKLBid8VI0DCcoBmBrTgp4VWTAXemH6YD",
            "contractor_code": CONTRACTOR_CODE,
            "name": NAME,
            "password": PASSWORD,
        }

        login_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://polanik.shop",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "referer": "https://panel.bachasport.pl/login",
        }
        
        # Авторизуемся на сайте и сохраняем куки в сессии
        response = session.post(login_url, data=login_payload, headers=login_headers)

        if response.status_code == 200:
            # Проверяем, успешно ли прошла авторизация (например, проверить наличие определенного элемента на странице)
            if "logout" in response.text.lower():  # Это пример, может потребоваться другая проверка
                logger.info("Успешная авторизация на сайте.")
                return session
            else:
                logger.error("Авторизация не удалась: неверные учетные данные или изменился интерфейс сайта.")
                return None
        else:
            logger.error(f"Ошибка при авторизации: статус {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сетевого запроса при авторизации: {e}")
        return None


def get_soup(html: str) -> BeautifulSoup:
    """
    Создает объект BeautifulSoup из HTML-кода.
    
    Args:
        html (str): HTML-код страницы.
        
    Returns:
        BeautifulSoup: Объект BeautifulSoup.
    """
    return BeautifulSoup(html, "lxml")


def fetch_html(session: requests.Session, url: str) -> Optional[str]:
    """
    Получает HTML-код страницы по указанному URL.
    
    Args:
        session (requests.Session): Сессия для выполнения запросов.
        url (str): URL страницы.
        
    Returns:
        Optional[str]: HTML-код страницы или None в случае ошибки.
    """
    try:
        response = session.get(url)
        if response.status_code == 200:
            logger.info(f"Успешно получен HTML с {url}")
            return response.text
        else:
            logger.error(f"Ошибка при получении HTML-кода страницы: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сетевого запроса при получении HTML: {e}")
        return None


def get_html_start(session: requests.Session, url: str = "https://panel.bachasport.pl") -> List[str]:
    """
    Получает HTML стартовой страницы и извлекает из неё ссылки для дальнейшего скрапинга.
    
    Args:
        session (requests.Session): Сессия для выполнения запросов.
        url (str): URL стартовой страницы.
        
    Returns:
        List[str]: Список URL для дальнейшего скрапинга или пустой список в случае ошибки.
    """
    html = fetch_html(session, url)
    if html:
        soup = get_soup(html)
        urls = get_scrape_start(soup)
        logger.info(f"Получены URL для скрапинга: {len(urls)} ссылок")
        return urls
    else:
        logger.error("Не удалось получить HTML стартовой страницы")
        return []


def get_scrape_start(soup: BeautifulSoup) -> List[str]:
    """
    Извлекает ссылки для скрапинга из объекта BeautifulSoup.
    
    Args:
        soup (BeautifulSoup): Объект BeautifulSoup с HTML-кодом страницы.
        
    Returns:
        List[str]: Список URL для скрапинга.
    """
    urls = []
    try:
        urls_tag = soup.find("ul", attrs={"class": "sidebar-menu sidebar-last"})
        if urls_tag:
            for li in urls_tag.find_all("li"):
                a_tag = li.find("a")
                if a_tag and a_tag.get("href"):
                    url = a_tag.get("href")
                    # Добавляем домен к относительному URL, если это необходимо
                    if not url.startswith("http"):
                        url = f"https://panel.bachasport.pl{url}"
                    urls.append(url)
        return urls
    except Exception as e:
        logger.error(f"Ошибка при извлечении ссылок: {e}")
        return urls


def random_pause(min_seconds: int = 3, max_seconds: int = 10) -> int:
    """
    Выполняет случайную паузу в заданном диапазоне.
    
    Args:
        min_seconds (int): Минимальная длительность паузы (целое число).
        max_seconds (int): Максимальная длительность паузы (целое число).
        
    Returns:
        int: Фактическая длительность паузы.
    """
    if min_seconds > max_seconds:
        raise ValueError("min_seconds не может быть больше max_seconds")

    pause_duration = random.randint(min_seconds, max_seconds)
    logger.info(f"Пауза {pause_duration} секунд.")
    time.sleep(pause_duration)
    return pause_duration


def scrape_pagination(session: requests.Session, start_url: str, max_pages: int = 10) -> List[dict]:
    """
    Скрапит данные со всех страниц пагинации.
    
    Args:
        session (requests.Session): Сессия для выполнения запросов.
        start_url (str): URL первой страницы.
        max_pages (int): Максимальное количество страниц для скрапинга.
        
    Returns:
        List[dict]: Список данных со всех страниц.
    """
    all_data = []
    current_url = start_url
    current_page = 1
    
    while current_page <= max_pages:
        logger.info(f"Скрапинг страницы {current_page}: {current_url}")
        
        html = fetch_html(session, current_url)
        if not html:
            logger.error(f"Не удалось получить HTML для страницы {current_page}")
            break
            
        soup = get_soup(html)
        
        # Здесь нужно реализовать извлечение данных с текущей страницы
        # page_data = extract_data_from_page(soup)
        # all_data.extend(page_data)
        
        # Найти ссылку на следующую страницу
        next_page_link = soup.find("a", {"rel": "next"})  # Пример, может отличаться
        if not next_page_link or not next_page_link.get("href"):
            logger.info(f"Достигнута последняя страница ({current_page})")
            break
            
        current_url = next_page_link.get("href")
        if not current_url.startswith("http"):
            current_url = f"https://panel.bachasport.pl{current_url}"
            
        current_page += 1
        
        # Делаем паузу между запросами
        random_pause()
        
    return all_data


def save_data_to_csv(data: List[dict], filename: str = "scraped_data.csv") -> None:
    """
    Сохраняет данные в CSV-файл.
    
    Args:
        data (List[dict]): Список словарей с данными.
        filename (str): Имя файла для сохранения.
    """
    filepath = data_directory / filename
    try:
        if not data:
            logger.warning("Нет данных для сохранения в CSV")
            return
            
        # Получаем заголовки из первого словаря
        fieldnames = data[0].keys()
        
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        logger.info(f"Данные успешно сохранены в {filepath}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в CSV: {e}")


def main():
    """
    Основная функция для запуска скрапинга.
    """
    try:
        # Получаем авторизованную сессию
        session = get_session()
        if not session:
            logger.critical("Не удалось получить сессию. Завершение программы.")
            return
        
        # Получаем ссылки со стартовой страницы
        urls = get_html_start(session)
        if not urls:
            logger.error("Не удалось получить ссылки для скрапинга. Завершение программы.")
            return
            
        logger.info(f"Найдено {len(urls)} ссылок для скрапинга")
        
        # Проходим по каждой ссылке и скрапим данные
        all_data = []
        for i, url in enumerate(urls):
            logger.info(f"Обработка ссылки {i+1}/{len(urls)}: {url}")
            
            # Скрапим данные с пагинацией
            data = scrape_pagination(session, url)
            all_data.extend(data)
            
            # Делаем паузу между обработкой разных разделов
            if i < len(urls) - 1:  # Не делаем паузу после последней ссылки
                random_pause(5, 15)
                
        # Сохраняем данные в CSV
        save_data_to_csv(all_data)
        
        logger.info("Скрапинг успешно завершен")
        
    except Exception as e:
        logger.critical(f"Критическая ошибка в основной функции: {e}")
        
        
if __name__ == "__main__":
    main()