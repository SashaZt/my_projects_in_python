# export_branches.py
import asyncio
import json
import os
from pathlib import Path

import aiohttp
from core.config import settings
from core.logger import logger
from models.branches import branches
from models.regions import cities, regions
from sqlalchemy import join, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Создаем engine для асинхронного подключения к БД
engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# async def export_branches_to_file(session: AsyncSession):
#     """
#     Экспортирует данные филиалов в текстовый файл в формате
#     id_{branche_id}_{city_name}_{region_name}

#     Args:
#         session: Сессия базы данных
#     """
#     try:
#         # Создаем сложный запрос с JOIN
#         query = select(
#             branches.c.branche_id,
#             branches.c.branche_name,
#             cities.c.name.label('city_name'),
#             regions.c.name.label('region_name')
#         ).select_from(
#             branches.join(
#                 cities, branches.c.city_id == cities.c.id, isouter=True
#             ).join(
#                 regions, branches.c.region_id == regions.c.id, isouter=True
#             )
#         )

#         result = await session.execute(query)
#         branches_data = result.fetchall()

#         # Создаем директорию для сохранения файла, если она не существует
#         output_dir = Path(os.environ.get('DATA_DIR', './data'))
#         output_dir.mkdir(parents=True, exist_ok=True)

#         # Путь к файлу
#         output_file = output_dir / 'all_branches.txt'

#         # Записываем данные в файл
#         with open(output_file, 'w', encoding='utf-8') as f:
#             for branch in branches_data:
#                 # Используем пустую строку, если какие-то поля None
#                 branche_id = branch.branche_id or ""
#                 city_name = (branch.city_name or "unknown_city").replace(" ", "_")
#                 region_name = (branch.region_name or "unknown_region").replace(" ", "_")

#                 # Форматируем строку
#                 line = f"id_{branche_id}_{city_name}_{region_name}\n"
#                 f.write(line)

#         logger.info(f"Экспорт филиалов завершен. Файл сохранен: {output_file}")
#     except Exception as e:
#         logger.error(f"Ошибка при экспорте филиалов: {e}")
#         raise
# async def export_cities_to_file(session: AsyncSession):
#     """
#     Экспортирует данные городов в текстовый файл в формате
#     {cities_id}_{region_id}_{name}

#     Args:
#         session: Сессия базы данных
#     """
#     try:
#         # Создаем простой запрос для получения данных о городах
#         query = select(
#             cities.c.id,
#             cities.c.region_id,
#             cities.c.name
#         )

#         result = await session.execute(query)
#         cities_data = result.fetchall()

#         # Создаем директорию для сохранения файла, если она не существует
#         output_dir = Path(os.environ.get('DATA_DIR', './data'))
#         output_dir.mkdir(parents=True, exist_ok=True)

#         # Путь к файлу
#         output_file = output_dir / 'all_cities.txt'

#         # Записываем данные в файл
#         with open(output_file, 'w', encoding='utf-8') as f:
#             for city in cities_data:
#                 # Используем пустую строку, если какие-то поля None
#                 city_id = str(city.id)
#                 region_id = str(city.region_id) if city.region_id else "0"
#                 name = (city.name or "unknown_city").replace(" ", "_")

#                 # Форматируем строку
#                 line = f"city_{city_id}_{region_id}_{name}\n"
#                 f.write(line)

#         logger.info(f"Экспорт городов завершен. Файл сохранен: {output_file}")
#     except Exception as e:
#         logger.error(f"Ошибка при экспорте городов: {e}")
#         raise
# export_branches.py


# Создаем engine для асинхронного подключения к БД
engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_branches_from_bts_api(session):
    """
    Получает данные о филиалах от API BTS

    Args:
        session: Сессия базы данных для получения данных о регионах и городах

    Returns:
        list: Список филиалов
    """
    # Получаем все города из БД для последовательного запроса
    query = select(cities.c.id)
    result = await session.execute(query)
    city_ids = [row.id for row in result.fetchall()]

    # Список всех филиалов
    all_branches = []

    # Токен для доступа к API BTS
    token = "bfeecb5d93cb62af861591f9a48bda02bb6c4ce9"

    # Заголовки запроса
    headers = {"Authorization": f"Bearer {token}"}

    # Получаем филиалы для каждого города
    async with aiohttp.ClientSession() as http_session:
        for city_id in city_ids:
            try:
                # Формируем URL для запроса
                url = f"http://api.bts.uz:8080/index.php?r=directory/branches-with-city&cityId={city_id}"

                # Выполняем запрос
                async with http_session.get(url, headers=headers) as response:
                    if response.status == 200:
                        response_data = await response.json()

                        # Если запрос успешен и есть данные
                        if response_data.get("code") == 200 and "data" in response_data:
                            branches = response_data["data"]
                            all_branches.extend(branches)

                            logger.info(
                                f"Получено {len(branches)} филиалов для города с ID {city_id}"
                            )
                        else:
                            logger.warning(
                                f"Нет данных для города с ID {city_id}: {response_data.get('message', '')}"
                            )
                    else:
                        logger.error(
                            f"Ошибка запроса для города с ID {city_id}: {response.status}"
                        )
            except Exception as e:
                logger.error(
                    f"Ошибка при получении филиалов для города с ID {city_id}: {e}"
                )

    return all_branches


async def export_branches_to_file(session: AsyncSession):
    """
    Экспортирует данные филиалов в текстовый файл в формате
    bts_{id}_{region_name}_{city_name}_{address_ru}
    """
    async with async_session() as session:
        try:
            # Получаем данные от API BTS
            branches = await get_branches_from_bts_api(session)

            # Создаем словари для кэширования данных о регионах и городах
            region_cache = {}
            city_cache = {}

            # Заполняем кэш данными о регионах
            query = select(regions.c.id, regions.c.name)
            result = await session.execute(query)
            for row in result.fetchall():
                region_cache[row.id] = row.name

            # Заполняем кэш данными о городах
            query = select(cities.c.id, cities.c.name)
            result = await session.execute(query)
            for row in result.fetchall():
                city_cache[row.id] = row.name

            # Создаем директорию для сохранения файла, если она не существует
            output_dir = Path(os.environ.get("DATA_DIR", "./data"))
            output_dir.mkdir(parents=True, exist_ok=True)

            # Путь к файлу
            output_file = output_dir / "all_branches.txt"

            # Записываем данные в файл
            with open(output_file, "w", encoding="utf-8") as f:
                for branch in branches:
                    # Получаем данные из филиала
                    branch_id = branch.get("id", "")
                    region_id = branch.get("regionId")
                    city_id = branch.get("cityId")
                    address_ru = branch.get("address_ru", "")

                    # Получаем имена региона и города из кэша
                    region_name = region_cache.get(region_id, "unknown_region")
                    city_name = city_cache.get(city_id, "unknown_city")

                    # Заменяем пробелы и специальные символы в именах
                    region_name = (
                        region_name.replace(" ", "_").replace(",", "").replace(".", "_")
                    )
                    city_name = (
                        city_name.replace(" ", "_").replace(",", "").replace(".", "_")
                    )

                    # Форматируем строку
                    line = f"bts_{branch_id}_{region_name}_{city_name}_{address_ru}\n"
                    f.write(line)

            logger.info(
                f"Экспорт филиалов завершен. Найдено {len(branches)} филиалов. Файл сохранен: {output_file}"
            )
        except Exception as e:
            logger.error(f"Ошибка при экспорте филиалов: {e}")
            raise


# # Функция для запуска скрипта
# async def main():
#     await export_branches_to_file()

# # Точка входа для запуска скрипта
# if __name__ == "__main__":
#     asyncio.run(main())
