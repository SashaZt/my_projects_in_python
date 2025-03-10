# app/api/v1/products.py
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.core.logger import logger
from app.models.product import Category, Manufacturer, Picture, Product
from app.schemas.product import (
    ProductCreate,
    ProductCreateInput,
    ProductResponseFormat,
)
from app.services.product import create_product

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def create_or_update_product(
    product: ProductCreate, db: AsyncSession = Depends(get_db)
):
    """Создать или обновить продукт"""
    logger.info(f"Создание/обновление продукта с ean: {product.ean}")
    try:
        db_product = await create_product(db, product)
        return {
            "message": f"Продукт с ean {product.ean} успешно создан или обновлен",
            "id": db_product.id,
        }
    except Exception as e:
        logger.error(
            f"Ошибка создания/обновления продукта с ean {product.ean}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/input/", response_model=Dict[str, Any])
async def create_or_update_product_with_input_format(
    input_data: ProductCreateInput, db: AsyncSession = Depends(get_db)
):
    """Создать или обновить продукт из формата с атрибутами"""
    ean = input_data.ean[0] if input_data.ean else ""
    logger.info(f"Создание/обновление продукта с ean: {ean}")
    
    try:
        # Преобразуем из нового формата в формат для create_product
        product_data = ProductCreate(
            ean=ean,
            title=input_data.attributes.get("title", [""])[0],
            description=input_data.attributes.get("description", [""])[0],
            manufacturer=input_data.attributes.get("manufacturer", [""])[0],
            category=input_data.attributes.get("category", [""])[0],
            pictures=input_data.attributes.get("picture", [])
        )
        
        db_product = await create_product(db, product_data)
        return {
            "message": f"Продукт с ean {ean} успешно создан или обновлен",
            "id": db_product.id,
        }
    except Exception as e:
        logger.error(f"Ошибка создания/обновления продукта с ean {ean}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{ean}", response_model=ProductResponseFormat)
async def get_product(ean: str, db: AsyncSession = Depends(get_db)):
    """Получить продукт по EAN"""
    logger.info(f"Извлечение продукта с помощью ean: {ean}")

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
        raise NotFoundError(detail=f"Product with EAN {ean} not found")

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


@router.get("/", response_model=ProductResponseFormat)
async def get_first_product(
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
        raise NotFoundError(detail="Products not found")

    # Берем первый продукт из результатов
    product = products[0]

    # Формируем ответ в нужном формате
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


@router.get("/all/list/", response_model=List[ProductResponseFormat])
async def get_all_products_array(db: AsyncSession = Depends(get_db)):
    """Получить все продукты в виде массива"""
    logger.info("Извлечение всех продуктов")
    
    # Строим запрос с загрузкой связанных данных
    query = select(Product).options(
        selectinload(Product.pictures),
        selectinload(Product.manufacturer),
        selectinload(Product.category)
    )
    
    # Выполняем запрос
    result = await db.execute(query)
    products = result.scalars().all()
    
    if not products:
        logger.warning("Продукты не найдены")
        raise NotFoundError(detail="Products not found")
    
    # Формируем массив продуктов в нужном формате
    response = []
    for product in products:
        formatted_product = {
            "ean": [product.ean],
            "attributes": {
                "title": [product.title],
                "manufacturer": [product.manufacturer.name if product.manufacturer else ""],
                "category": [product.category.name if product.category else ""],
                "description": [product.description or ""],
                "picture": [pic.url for pic in product.pictures]
            }
        }
        response.append(formatted_product)
    
    logger.info(f"Извлечено {len(products)} продуктов")
    return response