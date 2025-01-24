from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.core.base import Base  # Import Base from the new base.py
from sqlalchemy.orm import relationship


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    contact_type = Column(String(255), nullable=False)
    contact_status = Column(String(255), nullable=False)
    manager = Column(String(255))
    userphone = Column(String(20))
    useremail = Column(String(255))
    usersite = Column(String(255))
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с таблицей additional_contacts
    additional_contacts = relationship(
        "AdditionalContact", back_populates="contact", cascade="all, delete-orphan"
    )
