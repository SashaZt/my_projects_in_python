# app/models/product.py
"""
Модели данных для управления товарами, производителями, категориями и изображениями.

Используется SQLAlchemy ORM для определения структуры базы данных.
Каждый класс представляет отдельную таблицу в базе данных с определенными связями.
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Manufacturer(Base):
    """
    Модель производителя товаров.
    
    Атрибуты:
    - id: Уникальный идентификатор производителя
    - name: Название производителя (уникально)
    - products: Связь с товарами этого производителя
    """
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # Уникальное имя производителя

    # Обратная связь с товарами (один ко многим)
    products = relationship("Product", back_populates="manufacturer")


class Category(Base):
    """
    Модель категории товаров.
    
    Атрибуты:
    - id: Уникальный идентификатор категории
    - name: Название категории (уникально)
    - products: Связь с товарами этой категории
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # Уникальное имя категории

    # Обратная связь с товарами (один ко многим)
    products = relationship("Product", back_populates="category")


class Product(Base):
    """
    Модель товара.
    
    Атрибуты:
    - id: Уникальный идентификатор товара
    - ean: Уникальный штрих-код товара
    - title: Название товара
    - description: Описание товара (опционально)
    - manufacturer_id: Внешний ключ к производителю
    - category_id: Внешний ключ к категории
    - manufacturer: Связь с производителем
    - category: Связь с категорией
    - pictures: Связь с изображениями товара
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    ean = Column(
        String, nullable=False, unique=True
    )  # Уникальный EAN как идентификатор
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Внешние ключи для связей с производителем и категорией
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Определение связей с другими моделями
    manufacturer = relationship("Manufacturer", back_populates="products")
    category = relationship("Category", back_populates="products")
    pictures = relationship("Picture", back_populates="product")


class Picture(Base):
    """
    Модель изображения товара.
    
    Атрибуты:
    - id: Уникальный идентификатор изображения
    - url: URL изображения
    - product_id: Внешний ключ к товару
    - product: Связь с товаром
    
    Методы:
    - __repr__: Строковое представление объекта изображения
    """
    __tablename__ = "pictures"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)  # URL изображения
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Связь с товаром (многие к одному)
    product = relationship("Product", back_populates="pictures")

    def __repr__(self):
        """
        Возвращает строковое представление объекта Picture.
        
        Returns:
            str: Строка с id и url изображения
        """
        return f"<Picture(id={self.id}, url={self.url})>"