"""
vehicles.py

Handles vehicle-related API routes for the Dealer Management System.

This file allows dealers to:
- Decode VIN numbers
- Add vehicles to inventory
- View dealership inventory
- View individual vehicle financial information
- Calculate dashboard financial totals
- Mark vehicles as sold
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from pydantic import BaseModel, Field
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
# VEHICLE SALE REQUEST
# ==========================================

class VehicleSale(BaseModel):
    sale_price: float = Field(
        ...,
        gt=0
    )


# ==========================================
# GET ALL VEHICLES
# ==========================================

@router.get("/")
def get_vehicles(
    db: Session = Depends(get_db)
):

    vehicles = (
        db.query(models.Vehicle)
        .all()
    )

    return vehicles


# ==========================================
# DASHBOARD SUMMARY
# ==========================================

@router.get("/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db)
):
    """
    Calculate dealership dashboard totals.

    Expenses are included when calculating
    total investment and potential profit.
    """

    vehicles = (
        db.query(models.Vehicle)
        .all()
    )

    active_vehicles = [
        vehicle
        for vehicle in vehicles
        if vehicle.status != "sold"
    ]

    sold_vehicles = [
        vehicle
        for vehicle in vehicles
        if vehicle.status == "sold"
    ]


    # --------------------------------------
    # ACTIVE INVENTORY TOTALS
    # --------------------------------------

    total_invested = 0

    inventory_value = 0

    potential_profit = 0


    for vehicle in active_vehicles:

        investment = (
            calculate_total_investment(
                vehicle.purchase_price,
                vehicle.expenses
            )
        )

        projected_profit = (
            calculate_projected_profit(
                vehicle.purchase_price,
                vehicle.asking_price,
                vehicle.expenses
            )
        )

        total_invested += investment

        inventory_value += (
            vehicle.asking_price or 0
        )

        potential_profit += (
            projected_profit
        )


    # --------------------------------------
    # SOLD VEHICLE TOTALS
    # --------------------------------------

    total_sales = 0

    total_actual_profit = 0


    for vehicle in sold_vehicles:

        total_sales += (
            vehicle.sale_price or 0
        )

        actual_profit = (
            calculate_actual_profit(
                vehicle.purchase_price,
                vehicle.sale_price,
                vehicle.expenses
            )
        )

        total_actual_profit += (
            actual_profit or 0
        )


    return {
        "inventory_count":
            len(active_vehicles),

        "vehicles_sold":
            len(sold_vehicles),

        "total_invested":
            total_invested,

        "inventory_value":
            inventory_value,

        "potential_profit":
            potential_profit,

        "total_sales":
            total_sales,

        "total_actual_profit":
            total_actual_profit
    }


# ==========================================
# VIN DECODER
# ==========================================

@router.get("/decode/{vin}")
def get_vehicle_from_vin(
    vin: str
):

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

    clean_vin = (
        vehicle.vin
        .strip()
        .upper()
    )


    existing_vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.vin
            == clean_vin
        )
        .first()
    )


    if existing_vehicle:

        raise HTTPException(
            status_code=400,
            detail=(
                "A vehicle with this VIN "
                "already exists."
            )
        )


    vehicle_data = (
        vehicle.model_dump()
    )


    vehicle_data["vin"] = (
        clean_vin
    )


    new_vehicle = models.Vehicle(
        **vehicle_data
    )


    db.add(
        new_vehicle
    )

    db.commit()

    db.refresh(
        new_vehicle
    )


    return new_vehicle


# ==========================================
# MARK VEHICLE AS SOLD
# ==========================================

@router.put("/{vehicle_id}/sell")
def sell_vehicle(
    vehicle_id: int,
    sale: VehicleSale,
    db: Session = Depends(get_db)
):

    vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.id
            == vehicle_id
        )
        .first()
    )


    if not vehicle:

        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )


    if vehicle.status == "sold":

        raise HTTPException(
            status_code=400,
            detail=(
                "This vehicle is already "
                "marked as sold."
            )
        )


    vehicle.sale_price = (
        sale.sale_price
    )

    vehicle.status = (
        "sold"
    )


    db.commit()

    db.refresh(
        vehicle
    )


    total_expenses = (
        calculate_total_expenses(
            vehicle.expenses
        )
    )


    total_investment = (
        calculate_total_investment(
            vehicle.purchase_price,
            vehicle.expenses
        )
    )


    actual_profit = (
        calculate_actual_profit(
            vehicle.purchase_price,
            vehicle.sale_price,
            vehicle.expenses
        )
    )


    roi = (
        calculate_roi(
            vehicle.purchase_price,
            vehicle.sale_price,
            vehicle.expenses
        )
    )


    return {

        "message":
            "Vehicle marked as sold.",

        "vehicle":
            vehicle,

        "financials": {

            "total_expenses":
                total_expenses,

            "total_investment":
                total_investment,

            "sale_price":
                vehicle.sale_price,

            "actual_profit":
                actual_profit,

            "roi":
                roi
        }
    }


# ==========================================
# GET ONE VEHICLE
# ==========================================

@router.get("/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db)
):

    vehicle = (
        db.query(models.Vehicle)
        .filter(
            models.Vehicle.id
            == vehicle_id
        )
        .first()
    )


    if not vehicle:

        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )


    total_expenses = (
        calculate_total_expenses(
            vehicle.expenses
        )
    )


    total_investment = (
        calculate_total_investment(
            vehicle.purchase_price,
            vehicle.expenses
        )
    )


    projected_profit = (
        calculate_projected_profit(
            vehicle.purchase_price,
            vehicle.asking_price,
            vehicle.expenses
        )
    )


    actual_profit = (
        calculate_actual_profit(
            vehicle.purchase_price,
            vehicle.sale_price,
            vehicle.expenses
        )
    )


    roi = (
        calculate_roi(
            vehicle.purchase_price,
            vehicle.sale_price,
            vehicle.expenses
        )
    )


    return {

        "vehicle":
            vehicle,

        "financials": {

            "total_expenses":
                total_expenses,

            "total_investment":
                total_investment,

            "projected_profit":
                projected_profit,

            "actual_profit":
                actual_profit,

            "roi":
                roi
        }
    }
