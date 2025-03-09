# app/api/get_routes.py
from typing import Any, Dict, List, Optional

from app.db import get_db

# Используем централизованный логгер
from app.logger import logger
from app.models import Category, Manufacturer, Picture, Product
from app.schemas import Product as ProductSchema
from app.schemas import ProductResponseFormat  # Создайте эту схему, если еще не создали
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/products/{ean}", response_model=ProductResponseFormat)
async def get_product(ean: str, db: AsyncSession = Depends(get_db)):
    """Получить продукт по EAN"""
    logger.info(f"Извлечение продукта с помощью ean: {ean}")

    from sqlalchemy.orm import selectinload

    query = (
        select(Product)
        .options(
            selectinload(Product.pictures),
            selectinload(Product.manufacturer),
            selectinload(Product.category),
        )
        .filter_by(ean=ean)
    )

    result = await db.execute(query)
    product = result.scalar_one_or_none()

    if not product:
        logger.warning(f"Продукт с ean {ean} не найден")
        raise HTTPException(status_code=404, detail="Product not found")

    # Преобразуем продукт в нужный формат
    response = {
        "ean": [product.ean],
        "attributes": {
            "title": [product.title],
            "manufacturer": [product.manufacturer.name if product.manufacturer else ""],
            "category": [product.category.name if product.category else ""],
            "description": [product.description or ""],
            "picture": [pic.url for pic in product.pictures],
        },
    }

    logger.info(f"Продукт с ean {ean} успешно получен")
    return response


@router.get("/products/", response_model=ProductResponseFormat)
async def get_all_products(
    ean: Optional[str] = Query(None, description="EAN продукта для фильтрации"),
    db: AsyncSession = Depends(get_db),
):
    """Получить продукт по EAN или первый доступный"""
    logger.info(f"Извлечение продукта {ean if ean else 'первого доступного'}")

    # Строим запрос с загрузкой связанных данных
    query = select(Product).options(
        selectinload(Product.pictures),
        selectinload(Product.manufacturer),
        selectinload(Product.category),
    )

    # Применяем фильтр по EAN, если указан
    if ean:
        query = query.filter(Product.ean == ean)

    # Выполняем запрос
    result = await db.execute(query)
    products = result.scalars().all()

    if not products:
        logger.warning("Продукты не найдены")
        raise HTTPException(status_code=404, detail="Products not found")

    # Берем первый продукт из результатов
    product = products[0]

    # Формируем ответ в нужном формате (НЕ список!)
    response = {
        "ean": [product.ean],
        "attributes": {
            "title": [product.title],
            "manufacturer": [product.manufacturer.name if product.manufacturer else ""],
            "category": [product.category.name if product.category else ""],
            "description": [product.description or ""],
            "picture": [pic.url for pic in product.pictures],
        },
    }

    logger.info(f"Продукт {product.ean} успешно получен")
    return response


@router.get("/all_products/", response_model=List[ProductResponseFormat])
async def get_all_products_array(db: AsyncSession = Depends(get_db)):
    """
    Получить все продукты в виде массива
    """
    logger.info("Извлечение всех продуктов")

    # Строим запрос с загрузкой связанных данных
    query = select(Product).options(
        selectinload(Product.pictures),
        selectinload(Product.manufacturer),
        selectinload(Product.category),
    )

    # Выполняем запрос
    result = await db.execute(query)
    products = result.scalars().all()

    if not products:
        logger.warning("Продукты не найдены")
        raise HTTPException(status_code=404, detail="Products not found")

    # Формируем массив продуктов в нужном формате
    response = []
    for product in products:
        formatted_product = {
            "ean": [product.ean],
            "attributes": {
                "title": [product.title],
                "manufacturer": [
                    product.manufacturer.name if product.manufacturer else ""
                ],
                "category": [product.category.name if product.category else ""],
                "description": [product.description or ""],
                "picture": [pic.url for pic in product.pictures],
            },
        }
        response.append(formatted_product)

    logger.info(f"Извлечено {len(products)} продуктов")
    return response
