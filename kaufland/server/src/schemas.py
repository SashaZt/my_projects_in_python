# src/schemas.py
from pydantic import BaseModel

class ManufacturerBase(BaseModel):
    name: str

class CategoryBase(BaseModel):
    name: str

class PictureBase(BaseModel):
    url: str

class ProductCreate(BaseModel):
    ean: str
    title: str
    description: str | None = None
    manufacturer: str | None = None  # Имя производителя
    category: str | None = None      # Имя категории
    pictures: list[str]             # Список URL изображений

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