# models/__init__.py
from app.models.reservation import (  # Импорт новой модели
    Customer,
    Reservation,
    RoomReservation,
)

# from .telegram_recipients import TelegramRecipient  # Импорт новой модели
# from .telegram_sender import TelegramSender  # Импорт новой модели
from .additional_contacts import AdditionalContact  # Импорт новой модели
from .contact import Contact
from .telegram_message import TelegramMessage  # Импорт новой модели
from .telegram_users import TelegramUser  # Импорт новой модели
