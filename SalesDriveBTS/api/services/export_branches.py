# export_branches.py
import asyncio
import os
from pathlib import Path
from sqlalchemy import select, join
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.logger import logger
from core.config import settings
from models.branches import branches
from models.regions import regions, cities

# Создаем engine для асинхронного подключения к БД
engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def export_branches_to_file(session: AsyncSession):
    """
    Экспортирует данные филиалов в текстовый файл в формате
    id_{branche_id}_{city_name}_{region_name}
    
    Args:
        session: Сессия базы данных
    """
    try:
        # Создаем сложный запрос с JOIN
        query = select(
            branches.c.branche_id,
            branches.c.branche_name,
            cities.c.name.label('city_name'),
            regions.c.name.label('region_name')
        ).select_from(
            branches.join(
                cities, branches.c.city_id == cities.c.id, isouter=True
            ).join(
                regions, branches.c.region_id == regions.c.id, isouter=True
            )
        )
        
        result = await session.execute(query)
        branches_data = result.fetchall()
        
        # Создаем директорию для сохранения файла, если она не существует
        output_dir = Path(os.environ.get('DATA_DIR', './data'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Путь к файлу
        output_file = output_dir / 'all_branches.txt'
        
        # Записываем данные в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            for branch in branches_data:
                # Используем пустую строку, если какие-то поля None
                branche_id = branch.branche_id or ""
                city_name = (branch.city_name or "unknown_city").replace(" ", "_")
                region_name = (branch.region_name or "unknown_region").replace(" ", "_")
                
                # Форматируем строку
                line = f"id_{branche_id}_{city_name}_{region_name}\n"
                f.write(line)
        
        logger.info(f"Экспорт филиалов завершен. Файл сохранен: {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при экспорте филиалов: {e}")
        raise
async def export_cities_to_file(session: AsyncSession):
    """
    Экспортирует данные городов в текстовый файл в формате
    {cities_id}_{region_id}_{name}
    
    Args:
        session: Сессия базы данных
    """
    try:
        # Создаем простой запрос для получения данных о городах
        query = select(
            cities.c.id,
            cities.c.region_id,
            cities.c.name
        )
        
        result = await session.execute(query)
        cities_data = result.fetchall()
        
        # Создаем директорию для сохранения файла, если она не существует
        output_dir = Path(os.environ.get('DATA_DIR', './data'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Путь к файлу
        output_file = output_dir / 'all_cities.txt'
        
        # Записываем данные в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            for city in cities_data:
                # Используем пустую строку, если какие-то поля None
                city_id = str(city.id)
                region_id = str(city.region_id) if city.region_id else "0"
                name = (city.name or "unknown_city").replace(" ", "_")
                
                # Форматируем строку
                line = f"city_{city_id}_{region_id}_{name}\n"
                f.write(line)
        
        logger.info(f"Экспорт городов завершен. Файл сохранен: {output_file}")
    except Exception as e:
        logger.error(f"Ошибка при экспорте городов: {e}")
        raise