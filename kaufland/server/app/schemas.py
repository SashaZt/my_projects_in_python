# app/schemas.py
from typing import Any, Dict, List

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
    description: str | None = Field(None, max_length=2000)
    manufacturer: str | None = Field(None, max_length=255)
    category: str | None = Field(None, max_length=255)
    pictures: list[str] = Field(default_factory=list)

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
    description: str | None
    manufacturer: ManufacturerBase | None
    category: CategoryBase | None
    pictures: list[PictureBase]

    class Config:
        from_attributes = True
