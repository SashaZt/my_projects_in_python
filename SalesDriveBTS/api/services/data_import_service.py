# api/services/data_import_service.py
import json
import os
from pathlib import Path
from typing import List, Dict, Any

import asyncpg
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.logger import logger
from models.regions import regions, cities
from models.branches import branches

async def import_regions(db: AsyncSession, json_file_path: str) -> None:
    """
    Импортирует регионы из JSON файла в базу данных
    
    Args:
        db: Сессия базы данных
        json_file_path: Путь к JSON файлу с регионами
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(json_file_path):
            logger.warning(f"Файл с регионами не найден: {json_file_path}")
            return
        
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as file:
            regions_data = json.load(file)
        
        # Проверяем, есть ли уже регионы в базе
        result = await db.execute(select(regions).limit(1))
        existing_data = result.fetchone()
        
        # Если данных нет или принудительный импорт
        if not existing_data:
            # Подготавливаем данные для вставки
            values = []
            for region in regions_data:
                values.append({
                    "id": region['id'],
                    "name": region['name']
                })
            
            # Используем UPSERT (INSERT ... ON CONFLICT DO UPDATE)
            stmt = pg_insert(regions).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    "name": stmt.excluded.name,
                    "updated_at": stmt.excluded.updated_at
                }
            )
            
            await db.execute(stmt)
            await db.commit()
            
            logger.info(f"Загружено {len(regions_data)} регионов в базу данных")
        else:
            logger.info("Регионы уже загружены в базу данных")
            
    except Exception as e:
        logger.error(f"Ошибка при импорте регионов: {e}")
        await db.rollback()
        raise

async def import_cities(db: AsyncSession, json_file_path: str) -> None:
    """
    Импортирует города из JSON файла в базу данных
    
    Args:
        db: Сессия базы данных
        json_file_path: Путь к JSON файлу с городами
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(json_file_path):
            logger.warning(f"Файл с городами не найден: {json_file_path}")
            return
        
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as file:
            cities_data = json.load(file)
        
        # Проверяем, есть ли уже города в базе
        result = await db.execute(select(cities).limit(1))
        existing_data = result.fetchone()
        
        # Если данных нет или принудительный импорт
        if not existing_data:
            # Подготавливаем данные для вставки
            values = []
            for city in cities_data:
                values.append({
                    "id": city['id'],
                    "region_id": city['region_id'],
                    "name": city['name']
                })
            
            # Используем UPSERT (INSERT ... ON CONFLICT DO UPDATE)
            stmt = pg_insert(cities).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    "region_id": stmt.excluded.region_id,
                    "name": stmt.excluded.name,
                    "updated_at": stmt.excluded.updated_at
                }
            )
            
            await db.execute(stmt)
            await db.commit()
            
            logger.info(f"Загружено {len(cities_data)} городов в базу данных")
        else:
            logger.info("Города уже загружены в базу данных")
            
    except Exception as e:
        logger.error(f"Ошибка при импорте городов: {e}")
        await db.rollback()
        raise

async def import_branches(db: AsyncSession, json_file_path: str) -> None:
    """
    Импортирует филиалы из JSON файла в базу данных
    
    Args:
        db: Сессия базы данных
        json_file_path: Путь к JSON файлу с филиалами
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(json_file_path):
            logger.warning(f"Файл с филиалами не найден: {json_file_path}")
            return
        
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as file:
            branches_data = json.load(file)
        
        # Проверяем, есть ли уже филиалы в базе
        result = await db.execute(select(branches).limit(1))
        existing_data = result.fetchone()
        
        # Если данных нет или принудительный импорт
        if not existing_data:
            # Подготавливаем данные для вставки
            values = []
            for branch in branches_data:
                values.append({
                    "branche_id": branch['branche_id'],
                    "branche_name": branch['branche_name'],
                    "address": branch['address'],
                    "region_id": branch['regionId'],
                    "city_id": branch['cityId']
                })
            
            # Используем UPSERT (INSERT ... ON CONFLICT DO UPDATE)
            stmt = pg_insert(branches).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=['branche_id'],
                set_={
                    "branche_name": stmt.excluded.branche_name,
                    "address": stmt.excluded.address,
                    "region_id": stmt.excluded.region_id,
                    "city_id": stmt.excluded.city_id,
                    "updated_at": stmt.excluded.updated_at
                }
            )
            
            await db.execute(stmt)
            await db.commit()
            
            logger.info(f"Загружено {len(branches_data)} филиалов в базу данных")
        else:
            logger.info("Филиалы уже загружены в базу данных")
            
    except Exception as e:
        logger.error(f"Ошибка при импорте филиалов: {e}")
        await db.rollback()
        raise

async def import_all_data(db: AsyncSession) -> None:
    """
    Импортирует все справочные данные из JSON файлов
    
    Args:
        db: Сессия базы данных
    """
    # Путь к каталогу с JSON файлами
    data_dir = Path(os.environ.get('DATA_DIR', './data'))
    
    # Создаем каталог, если не существует
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Пути к JSON файлам
    regions_file = data_dir / 'regions.json'
    cities_file = data_dir / 'cities.json'
    branches_file = data_dir / 'all_branches.json'
    
    # Импортируем данные (в правильном порядке)
    await import_regions(db, str(regions_file))
    await import_cities(db, str(cities_file))
    await import_branches(db, str(branches_file))
    
    logger.info("Импорт справочных данных завершен")