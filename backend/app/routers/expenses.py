"""
expenses.py

Handles expense-related API routes for the Dealer Management System.
It allows dealers to add expenses to vehicles and track costs such as
repairs, transportation, auction fees, detailing, tires, and other expenses.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db


router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"]
)


# ==========================================
# ADD EXPENSE TO VEHICLE
# ==========================================

@router.post("/vehicle/{vehicle_id}")
def add_expense(
    vehicle_id: int,
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new expense to a specific vehicle.
    """

    vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.id == vehicle_id
        )
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )

    new_expense = models.Expense(
        vehicle_id=vehicle_id,
        category=expense.category,
        description=expense.description,
        amount=expense.amount
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return new_expense


# ==========================================
# GET VEHICLE EXPENSES
# ==========================================

@router.get("/vehicle/{vehicle_id}")
def get_vehicle_expenses(
    vehicle_id: int,
    db: Session = Depends(get_db)
):
    """
    Return all expenses connected to one vehicle.
    """

    vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.id == vehicle_id
        )
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )

    return vehicle.expenses
