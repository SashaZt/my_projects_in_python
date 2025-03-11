# app/services/base_crud.py
from typing import TypeVar, Generic, Type, Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.base import BaseModel as SQLAlchemyModel

ModelType = TypeVar("ModelType", bound=SQLAlchemyModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Базовый CRUD сервис с универсальными методами
    """

    def __init__(self, model: Type[ModelType]):
        """
        Инициализация CRUD сервиса

        :param model: SQLAlchemy модель
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Получение записи по ID

        :param db: Сессия базы данных
        :param id: Идентификатор записи
        :return: Найденная запись или None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Получение списка записей

        :param db: Сессия базы данных
        :param skip: Количество пропускаемых записей
        :param limit: Максимальное количество возвращаемых записей
        :return: Список записей
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """
        Создание новой записи

        :param db: Сессия базы данных
        :param obj_in: Схема для создания
        :return: Созданная запись
        """
        # Преобразование схемы в словарь
        obj_in_data = obj_in.model_dump(exclude_unset=True)

        # Создание модели
        db_obj = self.model(**obj_in_data)

        # Сохранение в базе данных
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """
        Обновление существующей записи

        :param db: Сессия базы данных
        :param db_obj: Существующая запись в базе
        :param obj_in: Схема для обновления
        :return: Обновленная запись
        """
        # Преобразование схемы в словарь
        update_data = obj_in.model_dump(exclude_unset=True)

        # Обновление полей
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # Сохранение изменений
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Удаление записи

        :param db: Сессия базы данных
        :param id: Идентификатор записи
        :return: Удаленная запись или None
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# # Пример использования для конкретной модели
# from app.models.crm import Contact, Order, Product, OrderItem, Delivery
# from app.schemas.crm import (
#     ContactCreate,
#     ContactUpdate,
#     OrderCreate,
#     OrderUpdate,
#     ProductCreate,
#     ProductUpdate,
#     OrderItemCreate,
#     OrderItemUpdate,
#     DeliveryCreate,
#     DeliveryUpdate,
# )

# # Создание CRUD-сервисов для каждой модели
# contact_crud = BaseCRUD[Contact, ContactCreate, ContactUpdate](Contact)
# order_crud = BaseCRUD[Order, OrderCreate, OrderUpdate](Order)
# product_crud = BaseCRUD[Product, ProductCreate, ProductUpdate](Product)
# order_item_crud = BaseCRUD[OrderItem, OrderItemCreate, OrderItemUpdate](OrderItem)
# delivery_crud = BaseCRUD[Delivery, DeliveryCreate, DeliveryUpdate](Delivery)
