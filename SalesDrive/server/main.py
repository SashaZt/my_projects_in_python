import asyncio
import logging
import json
import os
import sys
from pathlib import Path
from typing import Optional, Union
from loguru import logger
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.import_service import ImportService

current_directory = Path.cwd()
log_directory = current_directory / "log"
data_directory = current_directory / "data"

log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

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

async def import_from_file(file_path: Union[str, Path], session: AsyncSession) -> dict:
    """
    Импортирует данные из JSON-файла в базу данных.
    
    Args:
        file_path: Путь к JSON-файлу.
        session: Сессия базы данных.
        
    Returns:
        dict: Результат импорта с информацией об успешности и ошибках.
    """
    try:
        # Преобразуем в Path, если передана строка
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        # Проверяем существование файла
        if not file_path.exists():
            error_msg = f"File {file_path} does not exist"
            logger.error(error_msg)
            return {"success": False, "orders_imported": 0, "errors": [error_msg]}
        
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = file.read()
        
        # Импортируем данные
        import_service = ImportService(session)
        result = await import_service.import_from_json(json_data)
        
        # Проверяем результат
        if result["success"]:
            logger.info(f"Successfully imported {result['orders_imported']} orders from {file_path.name}")
        else:
            logger.error(f"Import failed for {file_path.name}: {result['errors']}")
        
        return result
    
    except Exception as e:
        error_msg = f"Error importing from file {file_path.name}: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "orders_imported": 0, "errors": [error_msg]}


async def import_from_directory(directory_path: Union[str, Path], pattern: str = "*.json", session: AsyncSession = None) -> dict:
    """
    Импортирует данные из всех JSON-файлов в указанной директории, соответствующих шаблону.
    
    Args:
        directory_path: Путь к директории с JSON-файлами.
        pattern: Шаблон для выбора файлов (по умолчанию "*.json").
        session: Сессия базы данных (если None, будет создана новая).
        
    Returns:
        dict: Сводный результат импорта.
    """
    # Преобразуем в Path, если передана строка
    if isinstance(directory_path, str):
        directory_path = Path(directory_path)
    
    # Проверяем существование директории
    if not directory_path.exists() or not directory_path.is_dir():
        error_msg = f"Directory {directory_path} does not exist or is not a directory"
        logger.error(error_msg)
        return {"success": False, "orders_imported": 0, "errors": [error_msg]}
    
    # Получаем список файлов
    files = list(directory_path.glob(pattern))
    
    if not files:
        logger.warning(f"No files matching pattern '{pattern}' found in {directory_path}")
        return {"success": True, "orders_imported": 0, "errors": []}
    
    # Если сессия не передана, создаем новую
    close_session = False
    if session is None:
        session_ctx = get_session()
        session = await session_ctx.__aenter__()
        close_session = True
    
    try:
        # Импортируем данные из каждого файла
        total_imported = 0
        total_errors = []
        
        for file_path in files:
            result = await import_from_file(file_path, session)
            total_imported += result.get("orders_imported", 0)
            if not result.get("success", False):
                total_errors.extend(result.get("errors", []))
        
        return {
            "success": len(total_errors) == 0,
            "orders_imported": total_imported,
            "files_processed": len(files),
            "errors": total_errors
        }
    
    finally:
        # Закрываем сессию, если мы её создали
        if close_session:
            await session_ctx.__aexit__(None, None, None)


async def main() -> None:
    """
    Основная функция приложения.
    """
    # Пример использования: либо из командной строки, либо программно
    if len(sys.argv) > 1:
        # Если передан аргумент командной строки, используем его как путь к файлу
        file_path = sys.argv[1]
        async with get_session() as session:
            await import_from_file(file_path, session)
    else:
        # Пример программного использования:
        # Настраиваем пути к данным
        recordings_output_file = data_directory / "recording_4.json"
        
        # Импортируем данные
        async with get_session() as session:
            result = await import_from_file(recordings_output_file, session)
            
            if result["success"]:
                logger.info(f"Import completed successfully: {result['orders_imported']} orders imported")
            else:
                logger.error(f"Import failed: {result['errors']}")


if __name__ == "__main__":
    asyncio.run(main())