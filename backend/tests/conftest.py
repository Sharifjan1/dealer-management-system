"""
conftest.py

Shared test setup. Every API test gets a fresh, empty in-memory
database, so tests never touch the real dealership.db file and
never affect each other.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


VALID_VIN = "1HGCM82633A004352"


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def make_vehicle(client):
    """Add a vehicle through the API and return its JSON."""

    def _make(vin=VALID_VIN, purchase_price=5000, asking_price=8000, **extra):
        payload = {
            "vin": vin,
            "purchase_price": purchase_price,
            "asking_price": asking_price,
            **extra,
        }
        response = client.post("/vehicles/", json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    return _make
