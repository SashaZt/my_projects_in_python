import json
import re
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from bs4 import BeautifulSoup
import pandas as pd
from logger import logger

# Глобальные переменные
current_directory = Path.cwd()
html_directory = current_directory / "html"
output_directory = current_directory / "output"

# Создаем необходимые директории
output_directory.mkdir(parents=True, exist_ok=True)

@dataclass
class CompanyData:
    """Класс для хранения данных компании"""
    edrpou_code: str = ""
    company_name: str = ""
    full_name: str = ""
    director: str = ""
    address: str = ""
    founding_date: str = ""
    authorized_capital: str = ""
    main_activity: str = ""
    other_activities: str = ""
    extraction_time: str = ""
    company_status: str = ""
    bankruptcy_date: str = ""
    
    # Данные о тендерах
    tenders_count: str = ""
    tenders_url: str = ""
    sales_data: Dict[str, str] = None
    
    # Финансовые данные по годам
    financial_data: Dict[str, Dict[str, str]] = None
    
    # Руководители и владельцы
    managers: List[Dict[str, str]] = None
    owners: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.financial_data is None:
            self.financial_data = {}
        if self.sales_data is None:
            self.sales_data = {}
        if self.managers is None:
            self.managers = []
        if self.owners is None:
            self.owners = []

def clean_text(text: str) -> str:
    """Очищает текст от лишних символов и пробелов"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def parse_company_status(soup: BeautifulSoup) -> str:
    """Парсит статус компании из alert блока"""
    company_status = ""
    
    # Ищем div с классом alert, который содержит статус компании
    alert_divs = soup.find_all('div', class_='alert')
    
    for alert_div in alert_divs:
        # Проверяем, есть ли в тексте упоминание статуса компании
        alert_text = alert_div.get_text(strip=True)
        if 'Статус компанії:' in alert_text:
            # Извлекаем статус после двоеточия
            status_match = re.search(r'Статус компанії:\s*(.+)', alert_text)
            if status_match:
                company_status = clean_text(status_match.group(1))
                break
    
    return company_status
def parse_bankruptcy_data(soup: BeautifulSoup) -> str:
    """Парсит данные о процедуре банкротства"""
    bankruptcy_date = ""
    
    # Ищем секцию с процедурой банкротства
    bankruptcy_section = soup.find('h3', string=lambda text: text and 'Процедура банкрутства' in text)
    if bankruptcy_section:
        section = bankruptcy_section.find_parent('section')
        if section:
            # Ищем дату в параграфе после заголовка
            date_paragraph = section.find('p')
            if date_paragraph:
                time_element = date_paragraph.find('time')
                if time_element:
                    bankruptcy_date = time_element.get('datetime', '') or clean_text(time_element.get_text())
    
    return bankruptcy_date

def parse_financial_data(soup: BeautifulSoup) -> Dict[str, Dict[str, str]]:
    """Парсит финансовые данные из таблицы"""
    financial_data = {}
    
    # Ищем таблицу с финансовыми показателями
    financial_section = soup.find('section', string=lambda text: text and 'Фінансові показники' in text)
    if not financial_section:
        financial_section = soup.find('h3', string=lambda text: text and 'Фінансові показники' in text)
        if financial_section:
            financial_section = financial_section.find_parent('section')
    
    if financial_section:
        table = financial_section.find('table')
        if table:
            # Получаем заголовки годов
            header_row = table.find('thead')
            years = []
            if header_row:
                th_elements = header_row.find_all('th')[1:]  # Пропускаем первую колонку
                years = [th.get_text(strip=True) for th in th_elements]
            
            # Получаем данные по строкам
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) > 1:
                        metric_name = cells[0].get_text(strip=True)
                        values = []
                        
                        for cell in cells[1:]:
                            data_element = cell.find('data')
                            if data_element and data_element.get('value'):
                                values.append(data_element.get('value'))
                            else:
                                text_value = clean_text(cell.get_text())
                                if text_value == '—' or text_value == '':
                                    values.append('')
                                else:
                                    values.append(text_value)
                        
                        # Связываем года с значениями
                        for i, year in enumerate(years):
                            if year not in financial_data:
                                financial_data[year] = {}
                            if i < len(values):
                                financial_data[year][metric_name] = values[i]
    
    return financial_data

def parse_tenders_data(soup: BeautifulSoup) -> tuple:
    """Парсит данные о тендерах и объемах продаж"""
    tenders_count = ""
    tenders_url = ""
    sales_data = {}
    
    # Ищем секцию с тендерами
    tenders_section = soup.find('h3', string=lambda text: text and 'Участь у тендерах' in text)
    if tenders_section:
        section = tenders_section.find_parent('section')
        if section:
            # Извлекаем количество тендеров и ссылку
            tenders_link = section.find('a', href=lambda href: href and 'tenders/company' in href)
            if tenders_link:
                tenders_url = tenders_link.get('href', '')
                # Извлекаем количество тендеров из текста ссылки
                span_element = tenders_link.find('span')
                if span_element:
                    tenders_text = clean_text(span_element.get_text())
                    # Извлекаем число из текста типа "2 тендери"
                    match = re.search(r'(\d+)', tenders_text)
                    if match:
                        tenders_count = match.group(1)
            
            # Парсим таблицу с объемами продаж
            table = section.find('table')
            if table:
                # Получаем заголовки годов
                header_row = table.find('thead')
                years = []
                if header_row:
                    th_elements = header_row.find_all('th')[1:]  # Пропускаем первую колонку
                    years = [th.get_text(strip=True) for th in th_elements]
                
                # Получаем данные по строкам
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['th', 'td'])
                        if len(cells) > 1:
                            metric_name = cells[0].get_text(strip=True)
                            
                            # Получаем значения по годам
                            for i, cell in enumerate(cells[1:]):
                                if i < len(years):
                                    year = years[i]
                                    data_element = cell.find('data')
                                    if data_element and data_element.get('value'):
                                        sales_data[f"{metric_name}_{year}"] = data_element.get('value')
                                    else:
                                        text_value = clean_text(cell.get_text())
                                        if text_value and text_value != '—':
                                            sales_data[f"{metric_name}_{year}"] = text_value
    
    return tenders_count, tenders_url, sales_data

def parse_managers_and_owners(soup: BeautifulSoup) -> tuple:
    """Парсит данные о руководителях и владельцах"""
    managers = []
    owners = []
    
    # Парсим руководителей
    managers_section = soup.find('dt', string=lambda text: text and 'Керівники' in text)
    if managers_section:
        manager_elements = managers_section.find_next_siblings('dd')
        for dd in manager_elements:
            if dd.find_next_sibling('dt'):  # Проверяем, не начался ли новый раздел
                break
            
            paragraphs = dd.find_all('p')
            if len(paragraphs) >= 2:
                name = clean_text(paragraphs[0].get_text())
                position = clean_text(paragraphs[1].get_text())
                additional = clean_text(paragraphs[2].get_text()) if len(paragraphs) > 2 else ""
                
                managers.append({
                    'name': name,
                    'position': position,
                    'additional': additional
                })
    
    # Парсим владельцев
    owners_section = soup.find('dt', string=lambda text: text and 'Власники' in text)
    if owners_section:
        owner_elements = owners_section.find_next_siblings('dd')
        for dd in owner_elements:
            if dd.find_next_sibling('dt'):  # Проверяем, не начался ли новый раздел
                break
            
            # Имя владельца (может быть ссылкой или текстом)
            name_element = dd.find('a') or dd.find('p')
            name = clean_text(name_element.get_text()) if name_element else ""
            
            # Роль
            paragraphs = dd.find_all('p')
            role = ""
            share_info = ""
            
            for p in paragraphs:
                text = clean_text(p.get_text())
                if 'Засновник' in text or 'Учасник' in text:
                    role = text
                
                # Информация о доле
                data_element = p.find('data')
                if data_element:
                    share_info = clean_text(p.get_text())
            
            owners.append({
                'name': name,
                'role': role,
                'share_info': share_info
            })
    
    return managers, owners

def parse_company_html(html_file_path: Path) -> Optional[CompanyData]:
    """Парсит HTML файл компании и извлекает данные"""
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        company_data = CompanyData()
        
        # Извлекаем код ЄДРПОУ из заголовка
        edrpou_h1 = soup.find('h1', class_='fs-2')
        if edrpou_h1:
            company_data.edrpou_code = clean_text(edrpou_h1.get_text())
        
        # Извлекаем название компании
        company_name_h2 = soup.find('h2', class_='fs-1')
        if company_name_h2:
            company_data.company_name = clean_text(company_name_h2.get_text())
        
        # Извлекаем директора из первой секции
        director_dd = soup.find('dt', string=lambda text: text and 'Директор' in text)
        if director_dd:
            director_element = director_dd.find_next_sibling('dd')
            if director_element:
                company_data.director = clean_text(director_element.get_text())
        
        # Парсим статус компании
        company_data.company_status = parse_company_status(soup)
        company_data.bankruptcy_date = parse_bankruptcy_data(soup)

        # Извлекаем регистрационные данные
        registration_section = soup.find('h3', string=lambda text: text and 'Реєстраційні дані' in text)
        if registration_section:
            section = registration_section.find_parent('section')
            if section:
                # Полное название
                full_name_dd = section.find('dt', string=lambda text: text and 'Повна назва' in text)
                if full_name_dd:
                    full_name_element = full_name_dd.find_next_sibling('dd')
                    if full_name_element:
                        company_data.full_name = clean_text(full_name_element.get_text())
                
                # Адрес
                address_dd = section.find('dt', string=lambda text: text and 'Адреса' in text)
                if address_dd:
                    address_element = address_dd.find_next_sibling('dd')
                    if address_element:
                        company_data.address = clean_text(address_element.get_text())
                
                # Дата основания
                founding_dd = section.find('dt', string=lambda text: text and 'Дата заснування' in text)
                if founding_dd:
                    founding_element = founding_dd.find_next_sibling('dd')
                    if founding_element:
                        time_element = founding_element.find('time')
                        if time_element:
                            company_data.founding_date = time_element.get('datetime', '') or clean_text(time_element.get_text())
                
                # Уставный капитал
                capital_dd = section.find('dt', string=lambda text: text and 'Статутний капітал' in text)
                if capital_dd:
                    capital_element = capital_dd.find_next_sibling('dd')
                    if capital_element:
                        data_element = capital_element.find('data')
                        if data_element:
                            company_data.authorized_capital = data_element.get('value', '') or clean_text(capital_element.get_text())
                
                # Основной вид деятельности
                main_activity_dd = section.find('dt', string=lambda text: text and 'Основний вид діяльності' in text)
                if main_activity_dd:
                    activity_element = main_activity_dd.find_next_sibling('dd')
                    if activity_element:
                        company_data.main_activity = clean_text(activity_element.get_text())
                
                # Другие виды деятельности
                other_activities_dd = section.find('dt', string=lambda text: text and 'Інші види діяльності' in text)
                if other_activities_dd:
                    other_activity_element = other_activities_dd.find_next_sibling('dd')
                    if other_activity_element:
                        company_data.other_activities = clean_text(other_activity_element.get_text())
                
                # Время извлечения
                extraction_dd = section.find('dt', string=lambda text: text and 'Час витягу з ЄДР' in text)
                if extraction_dd:
                    extraction_element = extraction_dd.find_next_sibling('dd')
                    if extraction_element:
                        time_element = extraction_element.find('time')
                        if time_element:
                            company_data.extraction_time = time_element.get('datetime', '') or clean_text(time_element.get_text())
        
        # Парсим финансовые данные
        company_data.financial_data = parse_financial_data(soup)
        
        # Парсим данные о тендерах
        company_data.tenders_count, company_data.tenders_url, company_data.sales_data = parse_tenders_data(soup)
        
        # Парсим руководителей и владельцев
        company_data.managers, company_data.owners = parse_managers_and_owners(soup)
        
        logger.info(f"Успешно обработан файл {html_file_path.name}")
        return company_data
        
    except Exception as e:
        logger.error(f"Ошибка при парсинге файла {html_file_path}: {str(e)}")
        return None

def save_to_json(companies_data: List[CompanyData], output_file: Path):
    """Сохраняет данные в JSON файл"""
    json_data = []
    
    for company in companies_data:
        if company:
            company_dict = {
                'edrpou_code': company.edrpou_code,
                'company_name': company.company_name,
                'full_name': company.full_name,
                'director': company.director,
                'address': company.address,
                'founding_date': company.founding_date,
                'authorized_capital': company.authorized_capital,
                'main_activity': company.main_activity,
                'other_activities': company.other_activities,
                'extraction_time': company.extraction_time,
                'company_status': company.company_status,
                'bankruptcy_date': company.bankruptcy_date,
                'tenders_count': company.tenders_count,
                'tenders_url': company.tenders_url,
                'sales_data': company.sales_data,
                'financial_data': company.financial_data,
                'managers': company.managers,
                'owners': company.owners
            }
            json_data.append(company_dict)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Данные сохранены в JSON файл: {output_file}")

def save_to_csv(companies_data: List[CompanyData], output_file: Path):
    """Сохраняет основные данные в CSV файл"""
    if not companies_data:
        return
    
    # Определяем все доступные года для финансовых данных
    all_years = set()
    for company in companies_data:
        if company and company.financial_data:
            all_years.update(company.financial_data.keys())
    
    all_years = sorted(all_years, reverse=True)
    
    # Определяем все финансовые метрики
    all_metrics = set()
    for company in companies_data:
        if company and company.financial_data:
            for year_data in company.financial_data.values():
                all_metrics.update(year_data.keys())
    
    # Создаем заголовки CSV
    headers = [
        'edrpou_code', 'company_name', 'full_name', 'director', 'address',
        'founding_date', 'authorized_capital', 'main_activity', 'other_activities',
        'extraction_time', 'company_status', 'bankruptcy_date', 'tenders_count', 'tenders_url' 
    ]

    
    # Добавляем заголовки для данных о продажах
    all_sales_keys = set()
    for company in companies_data:
        if company and company.sales_data:
            all_sales_keys.update(company.sales_data.keys())
    
    for sales_key in sorted(all_sales_keys):
        headers.append(f'sales_{sales_key}')
    
    # Добавляем заголовки для финансовых данных
    for year in all_years:
        for metric in sorted(all_metrics):
            headers.append(f'{metric}_{year}')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for company in companies_data:
            if company:
                row = [
                    company.edrpou_code,
                    company.company_name,
                    company.full_name,
                    company.director,
                    company.address,
                    company.founding_date,
                    company.authorized_capital,
                    company.main_activity,
                    company.other_activities,
                    company.extraction_time,
                    company.company_status,
                    company.bankruptcy_date,
                    company.tenders_count,
                    company.tenders_url
                ]
                
                # Добавляем данные о продажах
                for sales_key in sorted(all_sales_keys):
                    value = company.sales_data.get(sales_key, "") if company.sales_data else ""
                    row.append(value)
                
                # Добавляем финансовые данные
                for year in all_years:
                    for metric in sorted(all_metrics):
                        value = ""
                        if year in company.financial_data and metric in company.financial_data[year]:
                            value = company.financial_data[year][metric]
                        row.append(value)
                
                writer.writerow(row)
    
    logger.info(f"Данные сохранены в CSV файл: {output_file}")

def save_to_excel(companies_data: List[CompanyData], output_file: Path):
    """Сохраняет данные в Excel файл с несколькими листами"""
    if not companies_data:
        logger.warning("Нет данных для сохранения в Excel")
        return
    
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Лист 1: Основная информация о компаниях
            main_data = []
            for company in companies_data:
                if company:
                    main_data.append({
                        'ЄДРПОУ': company.edrpou_code,
                        'Назва компанії': company.company_name,
                        'Повна назва': company.full_name,
                        'Директор': company.director,
                        'Адреса': company.address,
                        'Дата заснування': company.founding_date,
                        'Статутний капітал': company.authorized_capital,
                        'Основний вид діяльності': company.main_activity,
                        'Інші види діяльності': company.other_activities,
                        'Час витягу з ЄДР': company.extraction_time,
                        'Статус компанії': company.company_status,
                        'Дата банкрутства': company.bankruptcy_date,
                        'Кількість тендерів': company.tenders_count,
                        'Посилання на тендери': company.tenders_url
                    })
                    
                    # Добавляем данные о продажах в основную таблицу
                    if company.sales_data:
                        for key, value in company.sales_data.items():
                            main_data[-1][f'Продажі_{key}'] = value
            
            if main_data:
                df_main = pd.DataFrame(main_data)
                df_main.to_excel(writer, sheet_name='Основна інформація', index=False)
                logger.info("Лист 'Основна інформація' створено")
            
            # Лист 2: Финансовые данные (сводная таблица)
            financial_pivot_data = []
            all_years = set()
            all_metrics = set()
            
            # Собираем все года и метрики
            for company in companies_data:
                if company and company.financial_data:
                    all_years.update(company.financial_data.keys())
                    for year_data in company.financial_data.values():
                        all_metrics.update(year_data.keys())
            
            all_years = sorted(all_years, reverse=True)
            all_metrics = sorted(all_metrics)
            
            # Создаем сводную таблицу финансовых данных
            for company in companies_data:
                if company:
                    row = {
                        'ЄДРПОУ': company.edrpou_code,
                        'Назва компанії': company.company_name
                    }
                    
                    # Добавляем финансовые данные по годам
                    for year in all_years:
                        for metric in all_metrics:
                            column_name = f'{metric} ({year})'
                            value = ""
                            if (company.financial_data and 
                                year in company.financial_data and 
                                metric in company.financial_data[year]):
                                value = company.financial_data[year][metric]
                            row[column_name] = value
                    
                    financial_pivot_data.append(row)
            
            if financial_pivot_data:
                df_financial_pivot = pd.DataFrame(financial_pivot_data)
                df_financial_pivot.to_excel(writer, sheet_name='Фінансові показники', index=False)
                logger.info("Лист 'Фінансові показники' створено")
            
            # Лист 3: Детальные финансовые данные (длинный формат)
            financial_detail_data = []
            for company in companies_data:
                if company and company.financial_data:
                    for year, metrics in company.financial_data.items():
                        for metric, value in metrics.items():
                            financial_detail_data.append({
                                'ЄДРПОУ': company.edrpou_code,
                                'Назва компанії': company.company_name,
                                'Рік': year,
                                'Показник': metric,
                                'Значення': value
                            })
            
            if financial_detail_data:
                df_financial_detail = pd.DataFrame(financial_detail_data)
                df_financial_detail.to_excel(writer, sheet_name='Детальні фінансові дані', index=False)
                logger.info("Лист 'Детальні фінансові дані' створено")
            
            # Лист 4: Руководители
            managers_data = []
            for company in companies_data:
                if company and company.managers:
                    for manager in company.managers:
                        managers_data.append({
                            'ЄДРПОУ': company.edrpou_code,
                            'Назва компанії': company.company_name,
                            'Ім\'я керівника': manager.get('name', ''),
                            'Посада': manager.get('position', ''),
                            'Додаткова інформація': manager.get('additional', '')
                        })
            
            if managers_data:
                df_managers = pd.DataFrame(managers_data)
                df_managers.to_excel(writer, sheet_name='Керівники', index=False)
                logger.info("Лист 'Керівники' створено")
            
            # Лист 5: Владельцы
            owners_data = []
            for company in companies_data:
                if company and company.owners:
                    for owner in company.owners:
                        owners_data.append({
                            'ЄДРПОУ': company.edrpou_code,
                            'Назва компанії': company.company_name,
                            'Ім\'я власника': owner.get('name', ''),
                            'Роль': owner.get('role', ''),
                            'Частка': owner.get('share_info', '')
                        })
            
            if owners_data:
                df_owners = pd.DataFrame(owners_data)
                df_owners.to_excel(writer, sheet_name='Власники', index=False)
                logger.info("Лист 'Власники' створено")
            
            # Лист 6: Тендеры и продажи
            tenders_data = []
            for company in companies_data:
                if company and (company.tenders_count or company.sales_data):
                    row = {
                        'ЄДРПОУ': company.edrpou_code,
                        'Назва компанії': company.company_name,
                        'Кількість тендерів': company.tenders_count,
                        'Посилання на тендери': company.tenders_url
                    }
                    
                    # Добавляем данные о продажах
                    if company.sales_data:
                        for key, value in company.sales_data.items():
                            row[key] = value
                    
                    tenders_data.append(row)
            
            if tenders_data:
                df_tenders = pd.DataFrame(tenders_data)
                df_tenders.to_excel(writer, sheet_name='Тендери та продажі', index=False)
                logger.info("Лист 'Тендери та продажі' створено")
        
        logger.info(f"Данные успешно сохранены в Excel файл: {output_file}")
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении в Excel: {str(e)}")

def save_financial_csv(companies_data: List[CompanyData], output_file: Path):
    """Сохраняет финансовые данные в отдельный CSV"""
    if not companies_data:
        return
    
    rows = []
    for company in companies_data:
        if company and company.financial_data:
            for year, metrics in company.financial_data.items():
                for metric, value in metrics.items():
                    rows.append({
                        'edrpou_code': company.edrpou_code,
                        'company_name': company.company_name,
                        'year': year,
                        'metric': metric,
                        'value': value
                    })
    
    if rows:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['edrpou_code', 'company_name', 'year', 'metric', 'value'])
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"Финансовые данные сохранены в CSV файл: {output_file}")

def json_to_excel(json_file_path: str, max_workers: int = 1):
    """Конвертирует JSON файл в Excel"""
    json_path = Path(json_file_path)
    
    if not json_path.exists():
        logger.error(f"JSON файл {json_file_path} не найден")
        return
    
    try:
        # Загружаем данные из JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        logger.info(f"Загружено {len(json_data)} записей из JSON файла")
        
        # Конвертируем в объекты CompanyData
        companies_data = []
        for item in json_data:
            company = CompanyData()
            company.edrpou_code = item.get('edrpou_code', '')
            company.company_name = item.get('company_name', '')
            company.full_name = item.get('full_name', '')
            company.director = item.get('director', '')
            company.address = item.get('address', '')
            company.founding_date = item.get('founding_date', '')
            company.authorized_capital = item.get('authorized_capital', '')
            company.main_activity = item.get('main_activity', '')
            company.other_activities = item.get('other_activities', '')
            company.extraction_time = item.get('extraction_time', '')
            company.company_status = item.get('company_status', '')
            company.bankruptcy_date = item.get('bankruptcy_date', '')
            company.tenders_count = item.get('tenders_count', '')
            company.tenders_url = item.get('tenders_url', '')
            company.sales_data = item.get('sales_data', {})
            company.financial_data = item.get('financial_data', {})
            company.managers = item.get('managers', [])
            company.owners = item.get('owners', [])
            
            companies_data.append(company)
        
        # Создаем имя Excel файла
        excel_file = json_path.parent / f"{json_path.stem}.xlsx"
        
        # Сохраняем в Excel
        save_to_excel(companies_data, excel_file)
        
        logger.info(f"Конвертация завершена: {excel_file}")
        
    except Exception as e:
        logger.error(f"Ошибка при конвертации JSON в Excel: {str(e)}")

def process_html_files(max_workers: int = 5):
    """Обрабатывает HTML файлы в многопоточном режиме"""
    
    # Получаем список HTML файлов
    html_files = list(html_directory.glob("*.html"))
    
    if not html_files:
        logger.warning(f"HTML файлы не найдены в директории {html_directory}")
        return
    
    logger.info(f"Найдено {len(html_files)} HTML файлов для обработки")
    logger.info(f"Используем {max_workers} потоков")
    
    companies_data = []
    processed_count = 0
    error_count = 0
    
    # Обрабатываем файлы в многопоточном режиме
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Запускаем задачи
        future_to_file = {
            executor.submit(parse_company_html, html_file): html_file 
            for html_file in html_files
        }
        
        # Обрабатываем результаты
        for future in as_completed(future_to_file):
            html_file = future_to_file[future]
            try:
                company_data = future.result()
                if company_data:
                    companies_data.append(company_data)
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Ошибка при обработке файла {html_file}: {str(e)}")
                error_count += 1
    
    # Сохраняем результаты
    if companies_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Сохраняем в JSON
        json_output = output_directory / f"companies_data_{timestamp}.json"
        save_to_json(companies_data, json_output)
        
        # Сохраняем в CSV
        csv_output = output_directory / f"companies_data_{timestamp}.csv"
        save_to_csv(companies_data, csv_output)
        
        # Сохраняем отдельный CSV только с финансовыми данными
        financial_csv = output_directory / f"financial_data_{timestamp}.csv"
        save_financial_csv(companies_data, financial_csv)
        
        # Сохраняем в Excel
        excel_output = output_directory / f"companies_data_{timestamp}.xlsx"
        save_to_excel(companies_data, excel_output)
    
    # Выводим статистику
    logger.info(f"Обработка завершена:")
    logger.info(f"Успешно обработано: {processed_count}")
    logger.info(f"Ошибок: {error_count}")
    logger.info(f"Всего файлов: {len(html_files)}")

def main():
    """Главная функция с парсингом аргументов командной строки"""
    parser = argparse.ArgumentParser(description='Парсинг HTML файлов компаний OpenDataBot')
    parser.add_argument('--threads', '-t', type=int, default=5, 
                       help='Количество потоков (по умолчанию: 5)')
    parser.add_argument('--json-to-excel', '-j', type=str, 
                       help='Конвертировать JSON файл в Excel (укажите путь к JSON файлу)')
    
    args = parser.parse_args()
    
    # Если указан параметр конвертации JSON в Excel
    if args.json_to_excel:
        json_to_excel(args.json_to_excel)
        return
    
    # Проверяем существование директории с HTML файлами
    if not html_directory.exists():
        logger.error(f"Директория {html_directory} не найдена")
        return
    
    # Запускаем обработку
    process_html_files(args.threads)

if __name__ == "__main__":
    main()