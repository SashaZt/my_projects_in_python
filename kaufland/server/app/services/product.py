# app/services/product.py
import json

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logger import logger
from app.models.product import Category, Manufacturer, Picture, Product
from app.schemas.product import ProductCreate


async def get_or_create_manufacturer(db: AsyncSession, name: str):
    result = await db.execute(select(Manufacturer).filter_by(name=name))
    manufacturer = result.scalar_one_or_none()
    if not manufacturer:
        manufacturer = Manufacturer(name=name)
        db.add(manufacturer)
        await db.flush()
    return manufacturer


async def get_or_create_category(db: AsyncSession, name: str):
    result = await db.execute(select(Category).filter_by(name=name))
    category = result.scalar_one_or_none()
    if not category:
        category = Category(name=name)
        db.add(category)
        await db.flush()
    return category


async def create_product(db: AsyncSession, product: ProductCreate):
    """
    Создание или обновление продукта с правильной обработкой транзакций
    """
    try:
        # Проверяем, существует ли продукт с таким ean
        result = await db.execute(select(Product).filter_by(ean=product.ean))
        db_product = result.scalar_one_or_none()

        if db_product:
            # Обновляем существующий продукт
            db_product.title = product.title
            db_product.description = product.description

            # Обрабатываем производителя
            if product.manufacturer:
                manufacturer = await get_or_create_manufacturer(db, product.manufacturer)
                db_product.manufacturer_id = manufacturer.id
            else:
                db_product.manufacturer_id = None

            # Обрабатываем категорию
            if product.category:
                category = await get_or_create_category(db, product.category)
                db_product.category_id = category.id
            else:
                db_product.category_id = None

            logger.info(f"Обновлен продукт с ean {product.ean}")
        else:
            # Создаём новый продукт
            manufacturer_id = None
            category_id = None

            if product.manufacturer:
                manufacturer = await get_or_create_manufacturer(db, product.manufacturer)
                manufacturer_id = manufacturer.id

            if product.category:
                category = await get_or_create_category(db, product.category)
                category_id = category.id

            db_product = Product(
                ean=product.ean,
                title=product.title,
                description=product.description,
                manufacturer_id=manufacturer_id,
                category_id=category_id,
            )
            db.add(db_product)
            await db.flush()
            logger.info(f"Создан продукт с ean {product.ean}")

        # Обновляем изображения (удаляем старые, добавляем новые)
        await db.execute(delete(Picture).where(Picture.product_id == db_product.id))

        # Добавляем новые изображения
        if product.pictures:
            pictures = [
                Picture(url=url, product_id=db_product.id) for url in product.pictures
            ]
            db.add_all(pictures)

        # Фиксируем изменения
        await db.commit()
        return db_product

    except Exception as e:
        # При ошибке откатываем транзакцию
        await db.rollback()
        logger.error(f"Ошибка при создании/обновлении продукта: {str(e)}")
        raise


async def import_products_from_json(db: AsyncSession, json_file: str):
    with open(json_file, "r") as f:
        data = json.load(f)

    product_data = {
        "ean": data["ean"][0],
        "title": data["attributes"]["title"][0],
        "description": (
            data["attributes"]["description"][0]
            if data["attributes"]["description"]
            else None
        ),
        "manufacturer": (
            data["attributes"]["manufacturer"][0]
            if data["attributes"]["manufacturer"]
            else None
        ),
        "category": (
            data["attributes"]["category"][0]
            if data["attributes"]["category"]
            else None
        ),
        "pictures": data["attributes"]["picture"],
    }
    product = ProductCreate(**product_data)
    await create_product(db, product)