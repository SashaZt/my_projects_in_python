from bs4 import BeautifulSoup
import json
from pathlib import Path
from config.logger import logger
import pandas as pd
current_directory = Path.cwd()
temp_directory = current_directory / "temp"
html_directory = temp_directory / "html"


def extract_contracts_from_xml(file_content):
    """
    Извлекает данные контрактов из XML файла с AJAX ответом
    """
    try:
        # Парсим XML
        soup = BeautifulSoup(file_content, 'xml')
        
        # Ищем update элемент с данными таблицы
        update_element = soup.find('update', id='form:table')
        if not update_element:
            logger.error("    ✗ Не найден элемент <update id='form:table'>")
            return []
        
        # Извлекаем CDATA содержимое
        cdata_content = update_element.get_text()
        if not cdata_content.strip():
            logger.error("    ✗ CDATA содержимое пустое")
            return []
                
        # Парсим HTML содержимое из CDATA
        html_soup = BeautifulSoup(cdata_content, 'html.parser')
        
        # Ищем все строки таблицы
        rows = html_soup.find_all('tr')
        
        contracts = []
        headers = ['№', 'Номер контракта', 'Закупающая организация', 'Поставщик(Подрядчик)', 'Тип', 'Дата подписания контракта']
        
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) >= 6:  # Убеждаемся что есть все нужные ячейки
                contract = {}
                
                for i, cell in enumerate(cells[:6]):  # Берем только первые 6 ячеек
                    # Удаляем все script теги
                    for script in cell.find_all('script'):
                        script.decompose()
                    
                    # Ищем ссылки для номера контракта
                    link = cell.find('a')
                    if link:
                        cell_text = link.get_text(strip=True)
                    else:
                        cell_text = cell.get_text(strip=True)
                    
                    # Очищаем лишние пробелы
                    cell_text = ' '.join(cell_text.split())
                    
                    contract[headers[i]] = cell_text
                
                # Добавляем только если есть данные
                if any(contract.values()) and contract.get('Номер контракта'):
                    contracts.append(contract)
        
        return contracts
        
    except Exception as e:
        logger.error(f"    ✗ Ошибка при парсинге XML: {e}")
        return []

def process_all_xml_files(html_directory):
    """
    Обрабатывает все HTML файлы из директории html_directory
    """

    # Ищем все HTML файлы (которые содержат XML)
    files = list(html_directory.glob("*.html"))
    
    print(f"Найдено {len(files)} файлов для обработки")
    
    all_contracts = []
    successful_files = 0
    total_records = 0
    
    for file_path in files:
        
        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, является ли это XML файлом
            if content.strip().startswith('<?xml'):
                contracts = extract_contracts_from_xml(content)
                
                if contracts:
                    all_contracts.extend(contracts)
                    successful_files += 1
                    total_records += len(contracts)
                else:
                    logger.error("    ✗ Записи не найдены")
            else:
                logger.error("    ! Не XML файл (пропускаем)")
                
        except Exception as e:
            logger.error(f"    ✗ Ошибка при обработке файла: {e}")
            continue
  
    # Сохраняем все контракты в JSON
    if all_contracts:
        save_contracts_to_json(all_contracts)

    return all_contracts

def save_contracts_to_json(contracts, filename='contracts_data.json'):
    """
    Сохраняет контракты в JSON файл
    """
    if not contracts:
        logger.error("Нет данных для сохранения")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(contracts, f, ensure_ascii=False, indent=4)
        
        logger.info(f"✓ Сохранено {len(contracts)} записей в файл {filename}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Ошибка при сохранении: {e}")
        return False


def scrap_company():
    all_data = []
    files = list(html_directory.glob("*.html"))
    # Пройтись по каждому HTML файлу в папке
    for html_file in files:
        with html_file.open(encoding="utf-8") as file:
            content = file.read()
        file_name = html_file.name.replace(".html", "")
        logger.info(f"Processing file: {file_name}")

        soup = BeautifulSoup(content, 'lxml')
        
        data_dict = {}
        data_dict["id_contract"] = file_name
        container = soup.find('div', class_='data-container')
        if container:
            rows = container.find_all('div', class_='row no-gutters reportHeader')
            for row in rows:
                label = row.find('span', class_='label label-group')
                value = row.find('div', class_='col-4 report-head')
                if label and value:
                    key = label.get_text(strip=True)
                    val = value.get_text(strip=True)
                    if key == 'Поставщик(Подрядчик)' and ' : ' in val:
                        # Разделяем Поставщик(Подрядчик) на ИНН и название
                        
                        inn, supplier = val.split(' : ', 1)
                        logger.info(inn.strip())
                        data_dict['ИНН'] = inn.strip()
                        data_dict['Поставщик(Подрядчик)'] = supplier.strip()
                    else:
                        # Сохраняем значение как есть, если это не Поставщик(Подрядчик) или нет разделителя
                        data_dict[key] = val
        
        table_data = []
        table = soup.find('table', class_='display-table private-room-table')
        if table:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                row_data = {
                    'Класс ОКГЗ': cells[0].get_text(strip=True),
                    'Сумма': cells[4].get_text(strip=True).replace('\xa0', '')
                }
                table_data.append(row_data)
        
        data_dict["items"] = table_data
        all_data.append(data_dict)
    
    return all_data

def merge_contracts(scraped_data, contracts_data_path):
    with open(contracts_data_path, 'r', encoding='utf-8') as f:
        contracts_data = json.load(f)
    
    merged_data = []
    for contract1 in scraped_data:
        contract_number = contract1.get("id_contract")
        for contract2 in contracts_data:
            if contract2.get("Номер контракта") == contract_number:
                merged_contract = {**contract1, **contract2}
                merged_data.append(merged_contract)
                break
    
    return merged_data
# Функция для преобразования данных в плоский формат с разделением items
def flatten_data(merged_data):
    flat_data = []
    # Находим максимальное количество элементов в items
    max_items = max(len(contract.get("items", [])) for contract in merged_data)
    
    for contract in merged_data:
        contract_base = {k: v for k, v in contract.items() if k != "items"}
        items = contract.get("items", [])
        
        # Создаем словарь для текущей записи
        flat_contract = contract_base.copy()
        
        # Добавляем элементы items в отдельные столбцы
        for i, item in enumerate(items, 1):
            flat_contract[f'Класс ОКГЗ {i}'] = item.get('Класс ОКГЗ', '')
            flat_contract[f'Сумма {i}'] = item.get('Сумма', '')
        
        # Заполняем оставшиеся столбцы пустыми значениями, если items меньше max_items
        for i in range(len(items) + 1, max_items + 1):
            flat_contract[f'Класс ОКГЗ {i}'] = ''
            flat_contract[f'Сумма {i}'] = ''
        
        flat_data.append(flat_contract)
    
    return flat_data, max_items

def main():
        # Получаем данные из HTML
    scraped_data = scrap_company()

    # Объединяем с contracts_data.json
    merged_data = merge_contracts(scraped_data, "contracts_data.json")

    # Преобразуем в плоский формат
    flat_data, max_items = flatten_data(merged_data)

    # Создаем DataFrame
    df = pd.DataFrame(flat_data)

    # Форматируем дату, если нужно (например, 2019-07-04 -> 04.07.2019)
    if 'Дата подписания контракта' in df:
        df['Дата подписания контракта'] = pd.to_datetime(
            df['Дата подписания контракта'], errors='coerce'
        ).dt.strftime('%d.%m.%Y')

    # Разделяем Поставщик(Подрядчик) на Поставщик(Подрядчик) и ИНН
    # Разделяем Поставщик(Подрядчик) на Поставщик(Подрядчик) и ИНН

    # if 'Поставщик(Подрядчик)' in df:
    #     # Разделяем по ": " (с пробелами), создаем DataFrame с expand=True
    #     split_supplier = df['Поставщик(Подрядчик)'].str.split(" : ", n=1, expand=True)
    #     # ИНН — первая часть, если есть разделение, иначе пустая строка
    #     df['ИНН'] = split_supplier[0].str.strip()
    #     # Поставщик(Подрядчик) — вторая часть, если есть, иначе исходная строка
    #     df['Поставщик(Подрядчик)'] = split_supplier[1].str.strip() if 1 in split_supplier.columns else split_supplier[0].str.strip()
    #     # Если разделение не произошло (ИНН и Поставщик совпадают), устанавливаем ИНН пустым
    #     df['ИНН'] = df['ИНН'].where(df['Поставщик(Подрядчик)'] != df['ИНН'], '')
    
    # Формируем список столбцов
    columns = [
    'id_contract', 'Тип', 'Номер объявления', 'Номер лота',
    'Поставщик(Подрядчик)', 'ИНН', 'Номер контракта', 'Дата подписания контракта',
    '№', 'Закупающая организация'
]

    # Добавляем столбцы для Класс ОКГЗ и Сумма
    for i in range(1, max_items + 1):
        columns.append(f'Класс ОКГЗ {i}')
        columns.append(f'Сумма {i}')

    # Реорганизуем столбцы
    df = df.reindex(columns=columns, fill_value='')

    # Записываем в Excel
    excel_file_path = "excel_file_path.xlsx"
    df.to_excel(excel_file_path, index=False, engine='openpyxl')
if __name__ == "__main__":
    main()