from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)
"""
models.py

This file defines the database models for the Dealer Management System.

It creates the structure for storing vehicle and expense information
in the database using SQLAlchemy.

The Vehicle model stores information such as VIN, year, make, model,
mileage, purchase price, asking price, sale price, and vehicle status.

The Expense model stores expenses associated with each vehicle, such as
repairs, transportation, auction fees, detailing, tires, and other costs.

Each vehicle can have multiple expenses, allowing the system to track
the total amount invested in a vehicle and later calculate profit and ROI.
"""

from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# VEHICLE MODEL

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Vehicle information
    vin = Column(
        String(17),
        unique=True,
        index=True,
        nullable=False
    )

    year = Column(String)
    make = Column(String)
    model = Column(String)
    trim = Column(String)
    body_type = Column(String)
    fuel_type = Column(String)

    color = Column(String)
    mileage = Column(Integer)

    # Financial information
    purchase_price = Column(
        Float,
        default=0
    )

    asking_price = Column(
        Float,
        default=0
    )

    sale_price = Column(
        Float,
        nullable=True
    )

    # Vehicle status:
    # inventory / sold / pending
    status = Column(
        String,
        default="inventory"
    )

    purchase_date = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # One vehicle can have many expenses
    expenses = relationship(
        "Expense",
        back_populates="vehicle",
        cascade="all, delete-orphan"
    )


# EXPENSE MODEL

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    vehicle_id = Column(
        Integer,
        ForeignKey("vehicles.id"),
        nullable=False
    )

    # Example:
    # Repair, Transportation,
    # Auction Fee, Detail, Tires, etc.
    category = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    amount = Column(
        Float,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    vehicle = relationship(
        "Vehicle",
        back_populates="expenses"
    )

## Chatgpt was used to help me out code this 

