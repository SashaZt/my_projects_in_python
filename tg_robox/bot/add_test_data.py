# scripts/add_test_data.py
import asyncio
import sys
import json
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.config import Config
from db.database import create_async_engine, get_session_maker
from db.models import RobloxProduct, CardCode, User


async def add_products_from_json():
    """Добавляет продукты из JSON-файла в базу данных"""
    # Загрузка конфигурации
    config = Config.load()

    # Подключение к БД
    engine = create_async_engine(config.db)
    session_maker = get_session_maker(engine)

    # Путь к JSON-файлу с продуктами
    json_path = ROOT_DIR / "data" / "robox_products.json"

    try:
        # Проверяем существование файла
        if not json_path.exists():
            print(f"Файл {json_path} не найден!")
            return

        # Читаем JSON-файл
        with open(json_path, "r", encoding="utf-8") as file:
            products_data = json.load(file)

        async with session_maker() as session:
            # Добавляем продукты из JSON
            added_products = []

            for product_data in products_data:
                product = RobloxProduct(
                    name=product_data["name"],
                    card_value=int(product_data["card_value"]),
                    card_count=product_data["card_count"],
                    robux_amount=product_data["robux_amount"],
                    price_uah=int(product_data["price_uah"]),
                    is_available=product_data["is_available"],
                )
                session.add(product)
                added_products.append(
                    (product_data["card_value"], product_data["card_count"])
                )

            await session.commit()

            print(f"Успешно добавлено {len(products_data)} продуктов в базу данных")

            # Для каждого продукта добавляем тестовые коды
            for card_value, card_count in added_products:
                # Добавляем по 5 кодов для каждого номинала
                for i in range(5):
                    code = CardCode(
                        card_value=float(card_value),
                        code=f"TEST-CODE-{card_value}-{i+1}",
                        is_used=False,
                        added_by=None,  # Тестовая система
                    )
                    session.add(code)

            await session.commit()

            print("Тестовые коды карт успешно добавлены в базу данных")

    except Exception as e:
        print(f"Ошибка при добавлении данных: {e}")


async def main():
    await add_products_from_json()


if __name__ == "__main__":
    asyncio.run(main())
