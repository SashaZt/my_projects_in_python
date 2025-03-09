# src/services.py
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import text  # Добавляем импорт text
from src.models import Product, Manufacturer, Category, Picture
from src.schemas import ProductCreate
from loguru import logger

async def get_or_create_manufacturer(db: AsyncSession, name: str):
    result = await db.execute(select(Manufacturer).filter_by(name=name))
    manufacturer = result.scalar_one_or_none()
    if not manufacturer:
        manufacturer = Manufacturer(name=name)
        db.add(manufacturer)
        await db.commit()
        await db.refresh(manufacturer)
    return manufacturer

async def get_or_create_category(db: AsyncSession, name: str):
    result = await db.execute(select(Category).filter_by(name=name))
    category = result.scalar_one_or_none()
    if not category:
        category = Category(name=name)
        db.add(category)
        await db.commit()
        await db.refresh(category)
    return category

async def create_product(db: AsyncSession, product: ProductCreate):
    # Проверяем, существует ли продукт с таким ean
    result = await db.execute(select(Product).filter_by(ean=product.ean))
    db_product = result.scalar_one_or_none()

    if db_product:
        # Обновляем существующий продукт
        db_product.title = product.title
        db_product.description = product.description
        db_product.manufacturer_id = (await get_or_create_manufacturer(db, product.manufacturer)).id if product.manufacturer else None
        db_product.category_id = (await get_or_create_category(db, product.category)).id if product.category else None
        await db.commit()
        await db.refresh(db_product)
        logger.info(f"Updated product with ean {product.ean}")
    else:
        # Создаём новый продукт
        manufacturer = await get_or_create_manufacturer(db, product.manufacturer) if product.manufacturer else None
        category = await get_or_create_category(db, product.category) if product.category else None
        db_product = Product(
            ean=product.ean,
            title=product.title,
            description=product.description,
            manufacturer_id=manufacturer.id if manufacturer else None,
            category_id=category.id if category else None
        )
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        logger.info(f"Created product with ean {product.ean}")

    # Обновляем изображения (удаляем старые, добавляем новые)
    await db.execute(text("DELETE FROM pictures WHERE product_id = :product_id"), {"product_id": db_product.id})
    pictures = [Picture(url=url, product_id=db_product.id) for url in product.pictures]
    db.add_all(pictures)
    await db.commit()

    return db_product

async def import_products_from_json(db: AsyncSession, json_file: str):
    with open(json_file, 'r') as f:
        data = json.load(f)

    product_data = {
        "ean": data["ean"][0],
        "title": data["attributes"]["title"][0],
        "description": data["attributes"]["description"][0] if data["attributes"]["description"] else None,
        "manufacturer": data["attributes"]["manufacturer"][0] if data["attributes"]["manufacturer"] else None,
        "category": data["attributes"]["category"][0] if data["attributes"]["category"] else None,
        "pictures": data["attributes"]["picture"]
    }
    product = ProductCreate(**product_data)
    await create_product(db, product)