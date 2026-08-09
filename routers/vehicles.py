"""
vehicles.py

Handles vehicle-related API routes for the Dealer Management System.
It allows dealers to decode VINs, add vehicles to inventory, view
vehicles, and see financial information such as investment and profit.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from vin_service import decode_vin
from calculations import (
    calculate_total_expenses,
    calculate_total_investment,
    calculate_projected_profit,
    calculate_actual_profit,
    calculate_roi
)


router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


# ==========================================
# GET ALL VEHICLES
# ==========================================

@router.get("/")
def get_vehicles(
    db: Session = Depends(get_db)
):
    """
    Return every vehicle currently stored
    in the dealership database.
    """

    vehicles = db.query(
        models.Vehicle
    ).all()

    return vehicles


# ==========================================
# VIN DECODER
# ==========================================

@router.get("/decode/{vin}")
def get_vehicle_from_vin(vin: str):
    """
    Decode a VIN and automatically retrieve
    vehicle information.
    """

    try:
        return decode_vin(vin)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ==========================================
# ADD VEHICLE
# ==========================================

@router.post("/")
def create_vehicle(
    vehicle: schemas.VehicleCreate,
    db: Session = Depends(get_db)
):
    """
    Add a new vehicle to dealership inventory.
    """

    clean_vin = vehicle.vin.strip().upper()

    existing_vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.vin == clean_vin
        )
        .first()
    )

    if existing_vehicle:
        raise HTTPException(
            status_code=400,
            detail="A vehicle with this VIN already exists."
        )

    vehicle_data = vehicle.model_dump()

    vehicle_data["vin"] = clean_vin

    new_vehicle = models.Vehicle(
        **vehicle_data
    )

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return new_vehicle


# ==========================================
# GET ONE VEHICLE
# ==========================================

@router.get("/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db)
):
    """
    Return one vehicle and calculate its
    current financial information.
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

    total_expenses = calculate_total_expenses(
        vehicle.expenses
    )

    total_investment = calculate_total_investment(
        vehicle.purchase_price,
        vehicle.expenses
    )

    projected_profit = calculate_projected_profit(
        vehicle.purchase_price,
        vehicle.asking_price,
        vehicle.expenses
    )

    actual_profit = calculate_actual_profit(
        vehicle.purchase_price,
        vehicle.sale_price,
        vehicle.expenses
    )

    roi = calculate_roi(
        vehicle.purchase_price,
        vehicle.sale_price,
        vehicle.expenses
    )

    return {
        "vehicle": vehicle,

        "financials": {
            "total_expenses": total_expenses,
            "total_investment": total_investment,
            "projected_profit": projected_profit,
            "actual_profit": actual_profit,
            "roi": roi
        }
    }
