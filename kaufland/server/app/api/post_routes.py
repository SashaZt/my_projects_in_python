# app/api/post_routes.py
from app.core.logger import logger
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas import ProductCreate, ProductCreateInput
from app.services import create_product

router = APIRouter()


@router.post("/products/", response_model=dict)
async def create_or_update_product(
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
            pictures=input_data.attributes.get("picture", []),
        )

        db_product = await create_product(db, product_data)
        return {
            "message": f"Продукт с ean {ean} успешно создан или обновлен",
            "id": db_product.id,
        }
    except Exception as e:
        logger.error(f"Ошибка создания/обновления продукта с ean {ean}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
