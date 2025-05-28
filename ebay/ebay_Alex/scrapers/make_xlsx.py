
import os
import json
import pandas as pd
from pathlib import Path
from config.logger import logger

def process_json_folders():
    """
    Обрабатывает все папки в temp/json/, объединяет JSON файлы в каждой папке
    и сохраняет результат в Excel файлы в temp/xlsx/
    """
    
    # Базовые пути
    json_base_path = Path("temp/json")
    xlsx_output_path = Path("temp/xlsx")
    
    # Создаем папку для xlsx файлов, если её нет
    xlsx_output_path.mkdir(parents=True, exist_ok=True)
    
    # Проверяем, существует ли папка с JSON
    if not json_base_path.exists():
        logger.error(f"Папка {json_base_path} не найдена!")
        return
    
    # Получаем все подпапки в temp/json/
    folders = [f for f in json_base_path.iterdir() if f.is_dir()]
    
    if not folders:
        logger.error("Подпапки в temp/json/ не найдены!")
        return
    
    logger.info(f"Найдено папок для обработки: {len(folders)}")
    
    # Обрабатываем каждую папку
    for folder in folders:
        folder_name = folder.name
        logger.info(f"\nОбрабатываю папку: {folder_name}")
        
        # Находим все JSON файлы в папке
        json_files = list(folder.glob("*.json"))
        
        if not json_files:
            logger.info(f"  JSON файлы в папке {folder_name} не найдены!")
            continue
        
        logger.info(f"  Найдено JSON файлов: {len(json_files)}")
        
        # Список для хранения всех данных
        all_data = []
        
        # Читаем каждый JSON файл
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data.append(data)
                    
            except json.JSONDecodeError as e:
                logger.error(f"  Ошибка чтения JSON файла {json_file.name}: {e}")
                continue
            except Exception as e:
                logger.error(f"  Неожиданная ошибка при чтении {json_file.name}: {e}")
                continue
        
        if not all_data:
            logger.error(f"  Не удалось прочитать данные из папки {folder_name}")
            continue
        
        # Создаем DataFrame из всех данных
        try:
            df = pd.DataFrame(all_data)
            
            # Путь для сохранения Excel файла
            excel_file_path = xlsx_output_path / f"{folder_name}.xlsx"
            
            # Сохраняем в Excel
            df.to_excel(excel_file_path, index=False, engine='openpyxl')
            
            logger.info(f"  Успешно создан файл: {excel_file_path}")
            logger.info(f"  Записано строк: {len(df)}")
            
        except Exception as e:
            logger.error(f"  Ошибка при создании Excel файла для папки {folder_name}: {e}")
            continue
    
    logger.info(f"\nОбработка завершена! Excel файлы сохранены в: {xlsx_output_path}")
if __name__ == "__main__":
    process_json_folders()