"""
schemas.py

Defines the data validation schemas for the Dealer Management System.
It controls the format of vehicle and expense information sent to
and returned from the API.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ==========================================
# VEHICLE SCHEMAS
# ==========================================

class VehicleCreate(BaseModel):
    vin: str = Field(
        ...,
        min_length=17,
        max_length=17
    )

    year: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None
    body_type: Optional[str] = None
    fuel_type: Optional[str] = None

    color: Optional[str] = None
    mileage: Optional[int] = Field(
        default=None,
        ge=0
    )

    purchase_price: float = Field(
        default=0,
        ge=0
    )

    asking_price: float = Field(
        default=0,
        ge=0
    )


class VehicleResponse(BaseModel):
    id: int
    vin: str

    year: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None

    color: Optional[str] = None
    mileage: Optional[int] = None

    purchase_price: float
    asking_price: float
    sale_price: Optional[float] = None

    status: str

    class Config:
        from_attributes = True


# EXPENSE SCHEMAS

class ExpenseCreate(BaseModel):
    category: str

    description: Optional[str] = None

    amount: float = Field(
        ...,
        gt=0
    )


class ExpenseResponse(BaseModel):
    id: int
    vehicle_id: int
    category: str
    description: Optional[str] = None
    amount: float

    class Config:
        from_attributes = True
      
