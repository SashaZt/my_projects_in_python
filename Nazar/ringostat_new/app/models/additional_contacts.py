from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base import Base


class AdditionalContact(Base):
    __tablename__ = "additional_contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # Обратная связь для получения информации об основном контакте
    contact = relationship("Contact", back_populates="additional_contacts")
