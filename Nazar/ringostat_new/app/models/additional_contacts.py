from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)  # Импорт типов данных и внешнего ключа.
from sqlalchemy.orm import relationship  # Для определения отношений между таблицами.
from app.core.base import Base  # Общий Base для всех моделей.


class AdditionalContact(Base):
    __tablename__ = "additional_contacts"  # Имя таблицы в базе данных.

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # Уникальный идентификатор записи.
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )  # Внешний ключ, ссылающийся на таблицу `contacts`. При удалении основного контакта связанные записи удаляются.
    name = Column(String(255), nullable=False)  # Имя дополнительного контакта.
    position = Column(String(255), nullable=True)  # Должность дополнительного контакта.
    phone = Column(
        String(20), nullable=True
    )  # Телефонный номер дополнительного контакта.
    email = Column(
        String(255), nullable=True
    )  # Электронная почта дополнительного контакта.

    # Обратная связь с таблицей `contacts`
    contact = relationship(
        "Contact",  # Имя связанной модели.
        back_populates="additional_contacts",  # Поле в модели `Contact`, описывающее обратную связь.
    )
