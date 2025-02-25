#!/usr/bin/env python3
"""
Website Monitor - инструмент для мониторинга изменений на большом количестве сайтов.
Отслеживает:
- Изменения веса (размера) главной страницы
- Изменения статуса ответа сервера

Инструмент проверяет сайты и записывает результаты в базу данных SQLite
для дальнейшего отслеживания истории изменений.
"""
import sys
import asyncio
import aiohttp
import sqlite3
import json
import datetime
from loguru import logger
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import csv
import time
from pathlib import Path

current_directory = Path.cwd()
log_directory = current_directory / "log"
data_directory = current_directory / "data"
RESULTS_DIR = current_directory / "results"
db_directory = current_directory / "db"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
db_directory.mkdir(parents=True, exist_ok=True)

DB_PATH  = db_directory / "website_monitor.db"
DOMAINS_FILE  = data_directory / "domains.txt"
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
# Конфигурация
MAX_CONCURRENT_REQUESTS = 100  # Ограничение количества одновременных запросов
REQUEST_TIMEOUT = 30  # Таймаут в секундах
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

# Создаем директорию для результатов, если она не существует
RESULTS_DIR.mkdir(exist_ok=True)

class WebsiteMonitor:
    def __init__(self, db_path: str):
        """Инициализация монитора сайтов"""
        self.db_path = db_path
        self.setup_database()
        
    def setup_database(self):
        """Создаёт базу данных и необходимые таблицы, если они не существуют"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для хранения данных о доменах
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY,
            domain TEXT UNIQUE NOT NULL
        )
        ''')
        
        # Таблица для хранения сканов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY,
            scan_date TIMESTAMP NOT NULL,
            description TEXT
        )
        ''')
        
        # Таблица для хранения результатов сканирования
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY,
            domain_id INTEGER NOT NULL,
            scan_id INTEGER NOT NULL,
            status_code INTEGER,
            page_size INTEGER,
            response_time REAL,
            last_modified TEXT,
            FOREIGN KEY (domain_id) REFERENCES domains (id),
            FOREIGN KEY (scan_id) REFERENCES scans (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("База данных создана или подключена успешно")
    
    def load_domains(self, filepath: str) -> List[str]:
        """Загружает список доменов из файла"""
        try:
            with open(filepath, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
            logger.info(f"Загружено {len(domains)} доменов из файла")
            return domains
        except Exception as e:
            logger.error(f"Ошибка при загрузке доменов: {e}")
            return []
    
    def save_domains_to_db(self, domains: List[str]):
        """Сохраняет список доменов в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for domain in domains:
            cursor.execute("INSERT OR IGNORE INTO domains (domain) VALUES (?)", (domain,))
        
        conn.commit()
        conn.close()
        logger.info(f"Домены сохранены в базу данных")
    
    def create_new_scan(self, description: str = "") -> int:
        """Создаёт новую запись сканирования и возвращает её id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        cursor.execute("INSERT INTO scans (scan_date, description) VALUES (?, ?)", (now, description))
        scan_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        logger.info(f"Создано новое сканирование с ID {scan_id} и датой {now}")
        return scan_id
    
    async def scan_website(self, session: ClientSession, domain: str) -> Dict[str, Any]:
        """Асинхронно сканирует один сайт и возвращает информацию о нём"""
        # Проверяем, содержит ли домен уже протокол
        if domain.startswith(('http://', 'https://')):
            url = domain
        else:
            url = f"https://{domain}"  # Сначала пробуем HTTPS
        
        start_time = time.time()
        
        try:
            async with session.get(url, allow_redirects=True) as response:
                status_code = response.status
                content = await response.read()
                page_size = len(content)
                response_time = time.time() - start_time
                last_modified = response.headers.get('Last-Modified', '')
                
                return {
                    "domain": domain,
                    "status_code": status_code,
                    "page_size": page_size,
                    "response_time": response_time,
                    "last_modified": last_modified,
                    "success": True
                }
        except Exception as e:
            logger.warning(f"Ошибка при сканировании {domain}: {e}")
            return {
                "domain": domain,
                "status_code": None,
                "page_size": None,
                "response_time": time.time() - start_time,
                "last_modified": "",
                "success": False,
                "error": str(e)
            }
    
    async def scan_all_websites(self, domains: List[str], scan_id: int) -> List[Dict[str, Any]]:
        """Асинхронно сканирует все сайты из списка"""
        results = []
        connector = TCPConnector(limit=MAX_CONCURRENT_REQUESTS, ssl=False)
        timeout = ClientTimeout(total=REQUEST_TIMEOUT)
        
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        async with ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            tasks = []
            for domain in domains:
                tasks.append(self.scan_website(session, domain))
            
            # Запуск сканирования всех доменов
            logger.info(f"Начинаю сканирование {len(domains)} доменов...")
            
            # Выполняем задачи пакетами, чтобы избежать перегрузки
            batch_size = 100
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i+batch_size]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Исключение при сканировании: {result}")
                    else:
                        results.append(result)
                
                logger.info(f"Обработано {min(i+batch_size, len(tasks))} из {len(tasks)} доменов")
        
        # Сохраняем результаты в базу данных
        self.save_scan_results(results, scan_id)
        
        return results
    
    def save_scan_results(self, results: List[Dict[str, Any]], scan_id: int):
        """Сохраняет результаты сканирования в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            domain = result["domain"]
            
            # Получаем id домена
            cursor.execute("SELECT id FROM domains WHERE domain = ?", (domain,))
            domain_row = cursor.fetchone()
            
            if domain_row:
                domain_id = domain_row[0]
                
                # Сохраняем результат сканирования
                cursor.execute("""
                INSERT INTO scan_results 
                (domain_id, scan_id, status_code, page_size, response_time, last_modified)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    domain_id, 
                    scan_id,
                    result.get("status_code"),
                    result.get("page_size"),
                    result.get("response_time"),
                    result.get("last_modified")
                ))
        
        conn.commit()
        conn.close()
        logger.info(f"Результаты сканирования сохранены в базу данных")
    
    def compare_with_previous_scan(self, current_scan_id: int) -> Tuple[List[Dict], List[Dict]]:
        """
        Сравнивает текущее сканирование с предыдущим и возвращает:
        1. Список сайтов, у которых изменился вес страницы
        2. Список сайтов, у которых изменился статус ответа
        """
        conn = sqlite3.connect(self.db_path)
        # Используем pandas для удобства работы с данными
        
        # Получаем предыдущий scan_id
        previous_scan_df = pd.read_sql_query(
            "SELECT id FROM scans WHERE id < ? ORDER BY id DESC LIMIT 1",
            conn,
            params=(current_scan_id,)
        )
        
        if previous_scan_df.empty:
            logger.info("Это первое сканирование, нет данных для сравнения")
            conn.close()
            return [], []
        
        previous_scan_id = previous_scan_df.iloc[0]['id']
        
        # Получаем текущие и предыдущие результаты
        query = """
        SELECT 
            d.domain,
            sr.status_code,
            sr.page_size,
            s.scan_date,
            s.id as scan_id
        FROM 
            scan_results sr
        JOIN 
            domains d ON sr.domain_id = d.id
        JOIN 
            scans s ON sr.scan_id = s.id
        WHERE 
            sr.scan_id IN (?, ?)
        """
        
        results_df = pd.read_sql_query(
            query,
            conn,
            params=(previous_scan_id, current_scan_id)
        )
        
        conn.close()
        
        # Разделяем на текущие и предыдущие результаты
        current_results = results_df[results_df['scan_id'] == current_scan_id].copy()
        previous_results = results_df[results_df['scan_id'] == previous_scan_id].copy()
        
        # Создаем словари для быстрого доступа
        current_dict = {row['domain']: row for _, row in current_results.iterrows()}
        previous_dict = {row['domain']: row for _, row in previous_results.iterrows()}
        
        # Находим изменения
        size_changes = []
        status_changes = []
        
        for domain, current in current_dict.items():
            if domain in previous_dict:
                previous = previous_dict[domain]
                
                # Проверка изменения размера
                if current['page_size'] != previous['page_size'] and current['page_size'] is not None and previous['page_size'] is not None:
                    size_diff = current['page_size'] - previous['page_size']
                    size_changes.append({
                        'domain': domain,
                        'previous_size': previous['page_size'],
                        'current_size': current['page_size'],
                        'diff': size_diff,
                        'diff_percentage': (size_diff / previous['page_size']) * 100 if previous['page_size'] > 0 else 0,
                        'scan_date': current['scan_date']
                    })
                
                # Проверка изменения статуса
                if current['status_code'] != previous['status_code']:
                    status_changes.append({
                        'domain': domain,
                        'previous_status': previous['status_code'],
                        'current_status': current['status_code'],
                        'scan_date': current['scan_date']
                    })
            
            # Новые домены (в текущем скане, но не в предыдущем)
            elif domain not in previous_dict and current['status_code'] is not None:
                status_changes.append({
                    'domain': domain,
                    'previous_status': None,
                    'current_status': current['status_code'],
                    'scan_date': current['scan_date'],
                    'note': 'New domain'
                })
        
        # Проверка доменов, которые исчезли
        for domain, previous in previous_dict.items():
            if domain not in current_dict and previous['status_code'] is not None:
                status_changes.append({
                    'domain': domain,
                    'previous_status': previous['status_code'],
                    'current_status': None,
                    'scan_date': previous['scan_date'],
                    'note': 'Domain disappeared'
                })
        
        logger.info(f"Найдено {len(size_changes)} изменений размера и {len(status_changes)} изменений статуса")
        return size_changes, status_changes
    
    def export_changes_to_csv(self, size_changes: List[Dict], status_changes: List[Dict]):
        """Экспортирует изменения в CSV файлы для дальнейшего использования"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Экспорт изменений размера
        if size_changes:
            size_changes_file = RESULTS_DIR / f"size_changes_{timestamp}.csv"
            with open(size_changes_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=size_changes[0].keys())
                writer.writeheader()
                writer.writerows(size_changes)
            logger.info(f"Изменения размера экспортированы в {size_changes_file}")
        
        # Экспорт изменений статуса
        if status_changes:
            status_changes_file = RESULTS_DIR / f"status_changes_{timestamp}.csv"
            with open(status_changes_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=status_changes[0].keys())
                writer.writeheader()
                writer.writerows(status_changes)
            logger.info(f"Изменения статуса экспортированы в {status_changes_file}")
        
        # Экспорт объединенных данных для дашборда
        all_changes = []
        
        for change in size_changes:
            all_changes.append({
                'domain': change['domain'],
                'change_type': 'size',
                'previous_value': change['previous_size'],
                'current_value': change['current_size'],
                'diff': change['diff'],
                'diff_percentage': change['diff_percentage'],
                'scan_date': change['scan_date']
            })
        
        for change in status_changes:
            all_changes.append({
                'domain': change['domain'],
                'change_type': 'status',
                'previous_value': change['previous_status'],
                'current_value': change['current_status'],
                'diff': None,
                'diff_percentage': None,
                'scan_date': change['scan_date'],
                'note': change.get('note', '')
            })
        
        if all_changes:
            dashboard_file = RESULTS_DIR / f"dashboard_data_{timestamp}.csv"
            with open(dashboard_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_changes[0].keys())
                writer.writeheader()
                writer.writerows(all_changes)
            logger.info(f"Данные для дашборда экспортированы в {dashboard_file}")
            
            # Создаем JSON для легкой интеграции с дашбордом
            dashboard_json = RESULTS_DIR / f"dashboard_data_{timestamp}.json"
            with open(dashboard_json, 'w') as f:
                json.dump(all_changes, f)
            logger.info(f"Данные для дашборда (JSON) экспортированы в {dashboard_json}")

def main():
    """Основная функция для запуска мониторинга"""
    monitor = WebsiteMonitor(DB_PATH)
    
    # Загрузка доменов
    domains = monitor.load_domains(DOMAINS_FILE)
    if not domains:
        logger.error(f"Не удалось загрузить домены из файла {DOMAINS_FILE}")
        return
    
    # Сохранение доменов в базу данных
    monitor.save_domains_to_db(domains)
    
    # Создание нового сканирования
    scan_id = monitor.create_new_scan(description="Ежемесячное сканирование сайтов")
    
    # Запуск сканирования
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(monitor.scan_all_websites(domains, scan_id))
    
    # Сравнение с предыдущим сканированием
    size_changes, status_changes = monitor.compare_with_previous_scan(scan_id)
    
    # Экспорт изменений в CSV
    if size_changes or status_changes:
        monitor.export_changes_to_csv(size_changes, status_changes)
        
        # Вывод статистики
        logger.info(f"Всего проверено сайтов: {len(domains)}")
        logger.info(f"Обнаружено изменений размера страницы: {len(size_changes)}")
        logger.info(f"Обнаружено изменений статуса ответа: {len(status_changes)}")
    else:
        logger.info("Изменений не обнаружено")

if __name__ == "__main__":
    main()