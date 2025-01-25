from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text  # Импорт типов колонок.
from app.core.base import Base  # Общий Base для всех моделей.
from sqlalchemy.orm import relationship  # Для определения отношений между таблицами.
from datetime import datetime, timezone


class Contact(Base):
    __tablename__ = "contacts"  # Имя таблицы в базе данных.

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # Уникальный идентификатор.
    username = Column(String(255), nullable=False)  # Имя пользователя или организации.
    contact_type = Column(
        String(255), nullable=False
    )  # Тип контакта (физлицо, компания и т.д.).
    contact_status = Column(
        String(255), nullable=False
    )  # Статус контакта (новый, активный и т.д.).
    manager = Column(String(255))  # Имя менеджера, закрепленного за контактом.
    userphone = Column(String(20))  # Телефонный номер контакта.
    useremail = Column(String(255))  # Электронная почта контакта.
    usersite = Column(String(255))  # Веб-сайт контакта.
    comment = Column(Text)  # Дополнительные комментарии.
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )  # Дата и время создания сообщения (с привязкой к UTC).

    # Связь с таблицей `additional_contacts`
    additional_contacts = relationship(
        "AdditionalContact",  # Имя связанной модели.
        back_populates="contact",  # Поле в связанной модели, описывающее обратную связь.
        cascade="all, delete-orphan",  # Удаление связанных записей при удалении основного контакта.
    )
