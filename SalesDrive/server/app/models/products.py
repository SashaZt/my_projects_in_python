from sqlalchemy import Column, Integer, String, Boolean, Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base, BaseModel


class Product(BaseModel):
    """Модель товара."""
    
    parameter = Column(String(50))
    text = Column(String(255))
    name_translate = Column(String(255), nullable=True)
    barcode = Column(String(50), nullable=True)
    keywords = Column(Text, nullable=True)
    document_name = Column(String(255), nullable=True)
    
    # Цены
    default_price = Column(Numeric(10, 2))
    cost_price = Column(Numeric(10, 2), nullable=True)
    
    # Статус
    active = Column(Boolean, default=True)
    
    # Физические характеристики
    mass = Column(Numeric(10, 2), nullable=True)
    volume = Column(Numeric(10, 2), nullable=True)
    length = Column(Numeric(10, 2), nullable=True)
    width = Column(Numeric(10, 2), nullable=True)
    height = Column(Numeric(10, 2), nullable=True)
    
    # Количество на складе
    rest_count = Column(Integer, default=0)
    
    # Валюта
    currency_id = Column(Integer, nullable=True)
    cost_price_currency_id = Column(Integer, nullable=True)
    
    # Информация о производителе
    manufacturer = Column(String(100), nullable=True)
    sku = Column(String(50), nullable=True)
    uktzed = Column(String(50), nullable=True)
    
    # Скидки
    discount = Column(Numeric(10, 2), nullable=True)
    percent_discount = Column(Numeric(10, 2), nullable=True)
    discount_period_from = Column(Date, nullable=True)
    discount_period_to = Column(Date, nullable=True)
    
    # Комплект
    is_complect = Column(Boolean, default=False)
    
    # Группа товаров
    product_group = Column(String(100), nullable=True)
    
    # Остатки на складах
    stock_balances = relationship("ProductStockBalance", back_populates="product", cascade="all, delete-orphan")
    
    # Компоненты комплекта
    complect_items = relationship("ProductComplect", 
                                  foreign_keys="ProductComplect.complect_id",
                                  back_populates="complect",
                                  cascade="all, delete-orphan")
    
    # Связь с заказами
    orders = relationship("OrderProduct", back_populates="product")


class ProductStockBalance(Base):
    """Модель остатков товаров на складах."""
    
    product_id = Column(Integer, ForeignKey("product.id"), primary_key=True)
    product = relationship("Product", back_populates="stock_balances")
    
    stock_id = Column(Integer, ForeignKey("stock.id"), primary_key=True)
    stock = relationship("Stock")
    
    quantity = Column(Integer, default=0)


class ProductComplect(BaseModel):
    """Модель компонентов комплекта товаров."""
    
    form_id = Column(Integer)
    
    complect_id = Column(Integer, ForeignKey("product.id"))
    complect = relationship("Product", foreign_keys=[complect_id], back_populates="complect_items")
    
    product_id = Column(Integer, ForeignKey("product.id"))
    product = relationship("Product", foreign_keys=[product_id])
    
    count = Column(Integer, default=1)


class OrderProduct(Base):
    """Модель товаров в заказе."""
    
    order_id = Column(Integer, ForeignKey("order.id"), primary_key=True)
    order = relationship("Order", back_populates="products")
    
    product_id = Column(Integer, ForeignKey("product.id"), primary_key=True)
    product = relationship("Product", back_populates="orders")
    
    product_name = Column(String(255))
    product_category = Column(String(100), nullable=True)
    
    quantity = Column(Integer, default=1)
    
    # Цены
    price = Column(Numeric(10, 2))
    discount = Column(Numeric(10, 2), nullable=True)
    percent_discount = Column(Numeric(10, 2), nullable=True)
    price_with_discount = Column(Numeric(10, 2))
    total_amount = Column(Numeric(10, 2))
    
    # Даты
    sale_date = Column(Date)
    day = Column(Integer)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)
    month_year = Column(String(7))
    
    # Тип продажи
    tip_prodazu = Column(String(100), nullable=True)