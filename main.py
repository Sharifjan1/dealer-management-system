"""
main.py

Starts the Dealer Management System backend API.
It connects the database, vehicle routes, and expense routes
and runs the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models

from database import engine
from routers import vehicles, expenses


# Create database tables
models.Base.metadata.create_all(
    bind=engine
)


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Dealer Management System API",
    description=(
        "Backend API for managing dealership inventory, "
        "vehicle expenses, VIN decoding, and profit calculations."
    ),
    version="1.0.0"
)


# ==========================================
# CORS SETTINGS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# CONNECT API ROUTES
# ==========================================

app.include_router(
    vehicles.router
)

app.include_router(
    expenses.router
)


# ==========================================
# HOME ROUTE
# ==========================================

@app.get("/")
def home():
    """
    Basic route used to confirm that
    the Dealer Management System API is running.
    """

    return {
        "message": "Dealer Management System API",
        "status": "running"
    }
