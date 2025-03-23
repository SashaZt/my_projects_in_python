from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from app.core.base import Base
import time


class Customer(Base):
    """Model for customer information."""
    __tablename__ = "customers"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    telephone = Column(String(255), nullable=True)
    remarks = Column(Text, nullable=True)

    # Relationship with Reservation
    reservations = relationship("Reservation", back_populates="customer")


class RoomReservation(Base):
    """Model for room reservation information."""
    __tablename__ = "room_reservations"

    roomReservationId = Column(String(255), primary_key=True, index=True)
    reservationId = Column(String(255), ForeignKey("reservations.id"), nullable=False)
    roomId = Column(String(255), nullable=False)
    categoryId = Column(Integer, nullable=False)
    arrival = Column(BigInteger, nullable=False)  # Изменено на BigInteger для больших значений времени
    departure = Column(BigInteger, nullable=False)  # Изменено на BigInteger для больших значений времени
    guestName = Column(String(255), nullable=False)
    numberOfGuests = Column(Integer, nullable=False)
    rateId = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    currencyCode = Column(String(10), nullable=False)
    invoice = Column(Float, nullable=False)
    paid = Column(Float, nullable=False)
    locked = Column(Boolean, default=False)
    detailed = Column(Boolean, default=False)
    addOns = Column(JSON, nullable=True, default=list)
    guestExtraCharges = Column(JSON, nullable=True, default=list)

    # Relationship with Reservation
    reservation = relationship("Reservation", back_populates="rooms")


class Reservation(Base):
    """Model for reservation information."""
    __tablename__ = "reservations"

    id = Column(String(255), primary_key=True, index=True)
    organizationId = Column(Integer, nullable=False)
    customerId = Column(String(255), ForeignKey("customers.id"), nullable=False)
    status = Column(String(50), nullable=False)
    services = Column(JSON, nullable=True, default=list)
    bookedAt = Column(BigInteger, nullable=False)  # Изменено на BigInteger для больших значений времени
    modifiedAt = Column(BigInteger, nullable=False)  # Изменено на BigInteger для больших значений времени
    source = Column(String(255), nullable=False)
    responsibleUserId = Column(Integer, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="reservations")
    rooms = relationship("RoomReservation", back_populates="reservation", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize reservation with current timestamps if not provided."""
        current_time = int(time.time() * 1000)  # Current time in milliseconds
        if 'bookedAt' not in kwargs:
            kwargs['bookedAt'] = current_time
        if 'modifiedAt' not in kwargs:
            kwargs['modifiedAt'] = current_time
        super().__init__(**kwargs)