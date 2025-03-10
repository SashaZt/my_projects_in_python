# app/schemas/product.py
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ManufacturerBase(BaseModel):
    name: str


class CategoryBase(BaseModel):
    name: str


class PictureBase(BaseModel):
    url: str


class ProductCreateInput(BaseModel):
    ean: List[str]
    attributes: Dict[str, List[Any]]


class ProductCreate(BaseModel):
    ean: str = Field(..., min_length=8, max_length=20)
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    manufacturer: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=255)
    pictures: List[str] = Field(default_factory=list)

    @validator("pictures")
    def validate_picture_urls(cls, urls):
        """Валидация URL изображений"""
        for url in urls:
            if not url.startswith(("http://", "https://")):
                raise ValueError(
                    "Все URL изображений должны начинаться с http:// или https://"
                )
        return urls


class ProductResponseFormat(BaseModel):
    ean: List[str]
    attributes: Dict[str, List[Any]]


class Product(BaseModel):
    id: int
    ean: str
    title: str
    description: Optional[str] = None
    manufacturer: Optional[ManufacturerBase] = None
    category: Optional[CategoryBase] = None
    pictures: List[PictureBase] = []

    class Config:
        from_attributes = True