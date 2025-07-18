# db/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    BigInteger,
    ForeignKey,
    TIMESTAMP,
    Text,
    JSON,
)
from sqlalchemy import CheckConstraint
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    BigInteger,
    ForeignKey,
    TIMESTAMP,
    Text,
    NUMERIC,
    JSON,
    DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """Модель для хранения информации о пользователях"""

    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), nullable=True)
    is_admin = Column(Boolean, default=False)
    registered_at = Column(TIMESTAMP, server_default=func.now())
    last_activity = Column(TIMESTAMP, nullable=True)

    # Отношения с другими таблицами
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"


class RobloxProduct(Base):
    """Модель для хранения информации о продуктах Roblox"""

    __tablename__ = "roblox_products"

    product_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    card_value = Column(NUMERIC(10), nullable=False)
    card_count = Column(Integer, nullable=False, default=1)
    robux_amount = Column(Integer, nullable=False)
    price_uah = Column(NUMERIC(10), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())

    # Отношения с другими таблицами
    orders = relationship("Order", back_populates="product")

    def __repr__(self):
        return f"<RobloxProduct(id={self.product_id}, name={self.name}, robux={self.robux_amount})>"


class CardCode(Base):
    """Модель для хранения кодов карт"""

    __tablename__ = "card_codes"

    code_id = Column(Integer, primary_key=True)
    card_value = Column(NUMERIC(10, 2), nullable=False)
    code = Column(String(255), nullable=False)
    is_used = Column(Boolean, default=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)
    added_by = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    added_at = Column(TIMESTAMP, server_default=func.now())
    used_at = Column(TIMESTAMP, nullable=True)

    # Отношения с другими таблицами
    order = relationship("Order", back_populates="card_codes")

    def __repr__(self):
        return f"<CardCode(id={self.code_id}, is_used={self.is_used})>"


class Order(Base):
    """Модель для хранения заказов"""

    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("roblox_products.product_id"))
    status = Column(String(50), default="created")  # created, paid, completed, canceled
    cards_required = Column(Integer, nullable=False, default=1)
    cards_issued = Column(Integer, nullable=False, default=0)
    total_price = Column(NUMERIC(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)

    # Отношения с другими таблицами
    user = relationship("User", back_populates="orders")
    product = relationship("RobloxProduct", back_populates="orders")
    payment = relationship("Payment", back_populates="order", uselist=False)
    card_codes = relationship("CardCode", back_populates="order")
    reviews = relationship("Review", back_populates="order")

    def __repr__(self):
        return (
            f"<Order(id={self.order_id}, user_id={self.user_id}, status={self.status})>"
        )


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), unique=True)
    amount = Column(NUMERIC(10, 2), nullable=False)
    status = Column(String(50), default="pending")
    
    # ДОБАВИТЬ эти поля, которые есть в БД:
    portmone_order_id = Column(String(255), nullable=True)
    payment_url = Column(String(512), nullable=True)
    payment_data = Column(JSON, nullable=True)  # В БД это JSONB
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())
    payment_date = Column(TIMESTAMP, nullable=True)
    
    # Отношения
    order = relationship("Order", back_populates="payment")

# class Review(Base):
#     """Модель для хранения отзывов пользователей"""

#     __tablename__ = "reviews"

#     review_id = Column(Integer, primary_key=True)
#     order_id = Column(Integer, ForeignKey("orders.order_id"))
#     user_id = Column(BigInteger, ForeignKey("users.user_id"))
#     rating = Column(Integer)  # Оценка от 1 до 5
#     comment = Column(Text, nullable=True)
#     created_at = Column(TIMESTAMP, server_default=func.now())

#     # Отношения с другими таблицами
#     order = relationship("Order", back_populates="reviews")
#     user = relationship("User", back_populates="reviews")

#     def __repr__(self):
#         return f"<Review(id={self.review_id}, user_id={self.user_id}, rating={self.rating})>"


class Statistic(Base):
    """Модель для хранения статистики"""

    __tablename__ = "statistics"

    stat_id = Column(Integer, primary_key=True)
    date = Column(TIMESTAMP, nullable=False)
    new_users = Column(Integer, default=0)
    orders_count = Column(Integer, default=0)
    successful_payments = Column(Integer, default=0)
    failed_payments = Column(Integer, default=0)
    total_revenue = Column(NUMERIC(12, 2), default=0)
    updated_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<Statistic(id={self.stat_id}, date={self.date}, revenue={self.total_revenue})>"


class Review(Base):
    """Модель отзыва пользователя"""

    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    rating = Column(Integer, CheckConstraint("rating BETWEEN 1 AND 5"))
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    is_approved = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)

    # Отношения
    order = relationship("Order", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
