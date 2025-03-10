# app/api/v1/__init__.py
from fastapi import APIRouter

from app.api.v1.products import router as products_router

api_router = APIRouter()

api_router.include_router(products_router, prefix="/products", tags=["Products"])