import json
import asyncio
import httpx
import os
from logger import logger
from typing import Dict, Any, Optional, List


current_directory = Path.cwd()
json_directory = current_directory / "json"
json_directory.mkdir(parents=True, exist_ok=True)

# Конфигурация
API_BASE_URL = "https://79.132.136.176:5000/api/v1"
PRODUCTS_ENDPOINT = f"{API_BASE_URL}/products/input/"
VERIFY_SSL = False  # Если используете самоподписанный сертификат

async def import_product(client: httpx.AsyncClient, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Импортирует данные о продукте в API.
    
    Args:
        client: httpx клиент для выполнения HTTP-запросов
        product_data: данные о продукте в формате JSON
        
    Returns:
        Ответ от API в случае успеха, None в случае ошибки
    """
    try:
        # Проверяем обязательные поля
        if not product_data.get('ean') or not product_data.get('attributes'):
            logger.error(f"Неверный формат данных: {product_data}")
            return None
            
        # Отправляем запрос в API
        response = await client.post(PRODUCTS_ENDPOINT, json=product_data, timeout=30.0)
        
        # Проверяем ответ
        if response.status_code in (200, 201):
            logger.info(f"Успешно импортирован продукт с EAN: {product_data['ean'][0]}")
            return response.json()
        else:
            logger.error(f"Ошибка при импорте продукта: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Исключение при импорте продукта: {str(e)}")
        return None

async def process_json_file(client: httpx.AsyncClient, file_path: str) -> Optional[Dict[str, Any]]:
    """
    Обрабатывает один JSON-файл и импортирует данные в API.
    
    Args:
        client: httpx клиент для выполнения HTTP-запросов
        file_path: путь к JSON-файлу с данными
        
    Returns:
        Результат импорта
    """
    # Проверяем существование файла
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        return None
        
    try:
        # Читаем JSON-файл
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                product_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Некорректный JSON в файле {file_path}")
                return None
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
        return None
    
    # Импортируем продукт
    result = await import_product(client, product_data)
    return result

async def process_directory(directory_path: str) -> List[Dict[str, Any]]:
    """
    Обрабатывает все JSON-файлы в указанной директории.
    
    Args:
        directory_path: путь к директории с JSON-файлами
        
    Returns:
        Список результатов импорта
    """
    if not os.path.isdir(directory_path):
        logger.error(f"Директория не найдена: {directory_path}")
        return []
    
    # Получаем список JSON-файлов
    json_files = [
        os.path.join(directory_path, f) 
        for f in os.listdir(directory_path) 
        if f.endswith('.json')
    ]
    
    if not json_files:
        logger.warning(f"JSON-файлы не найдены в директории: {directory_path}")
        return []
    
    results = []
    
    # Создаем HTTPX клиент
    async with httpx.AsyncClient(verify=VERIFY_SSL) as client:
        for file_path in json_files:
            logger.info(f"Обработка файла: {file_path}")
            result = await process_json_file(client, file_path)
            if result:
                results.append(result)
                print(f"Продукт успешно импортирован: {os.path.basename(file_path)}")
            else:
                print(f"Ошибка при импорте продукта: {os.path.basename(file_path)}")
    
    return results

async def main():
    """
    Основная функция для запуска импорта.
    """
    # Укажите здесь путь к файлу или директории
    path = "data/products"  # Замените на ваш путь
    
    if os.path.isdir(path):
        # Если это директория, обрабатываем все файлы
        logger.info(f"Начало обработки директории: {path}")
        results = await process_directory(path)
        logger.info(f"Всего успешно импортировано: {len(results)} продуктов")
    else:
        # Если это файл, обрабатываем только его
        logger.info(f"Начало обработки файла: {path}")
        async with httpx.AsyncClient(verify=VERIFY_SSL) as client:
            result = await process_json_file(client, path)
        
        if result:
            logger.info(f"Продукт успешно импортирован: {result}")
            print(f"Продукт успешно импортирован")
        else:
            logger.error(f"Не удалось импортировать продукт из файла {path}")
            print("Ошибка импорта. См. лог-файл для деталей.")

if __name__ == "__main__":
    asyncio.run(main())