# app/models.py
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

"""
    Manufacturer (Производители):
    Отдельная таблица с уникальными именами производителей (name).
    Связь "один-ко-многим" с таблицей products через manufacturer_id.
    Category (Категории):
    Отдельная таблица с уникальными именами категорий (name).
    Связь "один-ко-многим" с таблицей products через category_id.
    Product (Товары):
    Основная таблица с уникальным ean как идентификатором.
    title — обязательное поле.
    description — опциональное.
    Внешние ключи manufacturer_id и category_id связывают товар с производителем и категорией.
    Связь "один-ко-многим" с таблицей pictures через relationship.
    Picture (Изображения):
    Отдельная таблица для хранения URL-адресов изображений.
    Связь "многие-к-одному" с таблицей products через product_id.
    Каждый товар может иметь несколько изображений.
"""
Base = declarative_base()


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # Уникальное имя производителя

    products = relationship("Product", back_populates="manufacturer")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # Уникальное имя категории

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    ean = Column(
        String, nullable=False, unique=True
    )  # Уникальный EAN как идентификатор
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    manufacturer = relationship("Manufacturer", back_populates="products")
    category = relationship("Category", back_populates="products")
    pictures = relationship("Picture", back_populates="product")


class Picture(Base):
    __tablename__ = "pictures"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)  # URL изображения
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    product = relationship("Product", back_populates="pictures")

    def __repr__(self):
        return f"<Picture(id={self.id}, url={self.url})>"
