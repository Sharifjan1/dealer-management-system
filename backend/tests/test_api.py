"""
Tests for the API routes in app/routers/.

Each test uses the `client` fixture from conftest.py, which runs the
real FastAPI app against an empty in-memory database.
"""

import pytest

from app.routers import vehicles as vehicles_router
from tests.conftest import VALID_VIN

OTHER_VIN = "2HGFC2F59HH500311"


# ---------- Home ----------

def test_home_says_running(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


# ---------- Adding vehicles ----------

def test_add_vehicle(client):
    response = client.post(
        "/vehicles/",
        json={
            "vin": VALID_VIN,
            "year": "2003",
            "make": "Honda",
            "model": "Accord",
            "mileage": 150000,
            "purchase_price": 2500,
            "asking_price": 4495,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] > 0
    assert body["vin"] == VALID_VIN
    assert body["status"] == "inventory"
    assert body["sale_price"] is None
    assert body["asking_price"] == 4495


def test_vin_is_saved_in_uppercase(client, make_vehicle):
    vehicle = make_vehicle(vin=VALID_VIN.lower())
    assert vehicle["vin"] == VALID_VIN


def test_duplicate_vin_is_rejected(client, make_vehicle):
    make_vehicle()
    response = client.post("/vehicles/", json={"vin": VALID_VIN})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_duplicate_vin_is_caught_even_in_lowercase(client, make_vehicle):
    make_vehicle()
    response = client.post("/vehicles/", json={"vin": VALID_VIN.lower()})
    assert response.status_code == 400


@pytest.mark.parametrize("vin", ["SHORT", VALID_VIN + "X"])
def test_vin_must_be_17_characters(client, vin):
    response = client.post("/vehicles/", json={"vin": vin})
    assert response.status_code == 422


@pytest.mark.parametrize("field", ["purchase_price", "asking_price", "mileage"])
def test_negative_numbers_are_rejected(client, field):
    response = client.post("/vehicles/", json={"vin": VALID_VIN, field: -1})
    assert response.status_code == 422


def test_list_vehicles(client, make_vehicle):
    make_vehicle(vin=VALID_VIN)
    make_vehicle(vin=OTHER_VIN)
    response = client.get("/vehicles/")
    assert response.status_code == 200
    vins = {v["vin"] for v in response.json()}
    assert vins == {VALID_VIN, OTHER_VIN}


def test_list_is_empty_on_a_new_lot(client):
    assert client.get("/vehicles/").json() == []


# ---------- One vehicle ----------

def test_missing_vehicle_returns_404(client):
    response = client.get("/vehicles/9999")
    assert response.status_code == 404


def test_vehicle_financials_before_sale(client, make_vehicle):
    vehicle = make_vehicle(purchase_price=5000, asking_price=8000)
    client.post(f"/expenses/vehicle/{vehicle['id']}", json={"category": "Detail", "amount": 150})
    client.post(f"/expenses/vehicle/{vehicle['id']}", json={"category": "Repair", "amount": 350})

    response = client.get(f"/vehicles/{vehicle['id']}")
    assert response.status_code == 200
    body = response.json()

    assert body["vehicle"]["vin"] == VALID_VIN
    money = body["financials"]
    assert money["total_expenses"] == 500
    assert money["total_investment"] == 5500
    assert money["projected_profit"] == 2500
    assert money["actual_profit"] is None
    assert money["roi"] is None


# ---------- Selling ----------

def test_sell_vehicle(client, make_vehicle):
    vehicle = make_vehicle(purchase_price=5000, asking_price=8000)
    client.post(f"/expenses/vehicle/{vehicle['id']}", json={"category": "Detail", "amount": 500})

    response = client.put(f"/vehicles/{vehicle['id']}/sell", json={"sale_price": 7800})
    assert response.status_code == 200
    body = response.json()

    assert body["vehicle"]["status"] == "sold"
    assert body["vehicle"]["sale_price"] == 7800
    assert body["financials"]["actual_profit"] == 2300
    assert body["financials"]["roi"] == pytest.approx(2300 / 5500 * 100)


def test_cannot_sell_twice(client, make_vehicle):
    vehicle = make_vehicle()
    client.put(f"/vehicles/{vehicle['id']}/sell", json={"sale_price": 7800})
    response = client.put(f"/vehicles/{vehicle['id']}/sell", json={"sale_price": 9000})
    assert response.status_code == 400
    assert "already" in response.json()["detail"]


def test_sale_price_must_be_above_zero(client, make_vehicle):
    vehicle = make_vehicle()
    response = client.put(f"/vehicles/{vehicle['id']}/sell", json={"sale_price": 0})
    assert response.status_code == 422


def test_selling_missing_vehicle_returns_404(client):
    response = client.put("/vehicles/9999/sell", json={"sale_price": 1000})
    assert response.status_code == 404


# ---------- Expenses ----------

def test_add_and_list_expenses(client, make_vehicle):
    vehicle = make_vehicle()
    response = client.post(
        f"/expenses/vehicle/{vehicle['id']}",
        json={"category": "Tires", "description": "Two front tires", "amount": 260},
    )
    assert response.status_code == 200
    created = response.json()
    assert created["vehicle_id"] == vehicle["id"]
    assert created["amount"] == 260

    listing = client.get(f"/expenses/vehicle/{vehicle['id']}")
    assert listing.status_code == 200
    assert [e["category"] for e in listing.json()] == ["Tires"]


def test_expense_amount_must_be_above_zero(client, make_vehicle):
    vehicle = make_vehicle()
    response = client.post(f"/expenses/vehicle/{vehicle['id']}", json={"category": "Detail", "amount": 0})
    assert response.status_code == 422


def test_expense_for_missing_vehicle_returns_404(client):
    response = client.post("/expenses/vehicle/9999", json={"category": "Detail", "amount": 100})
    assert response.status_code == 404
    assert client.get("/expenses/vehicle/9999").status_code == 404


# ---------- Dashboard ----------

def test_dashboard_on_empty_lot(client):
    body = client.get("/vehicles/dashboard/summary").json()
    assert body["inventory_count"] == 0
    assert body["vehicles_sold"] == 0
    assert body["total_invested"] == 0
    assert body["total_actual_profit"] == 0


def test_dashboard_totals(client, make_vehicle):
    on_lot = make_vehicle(vin=VALID_VIN, purchase_price=5000, asking_price=8000)
    sold = make_vehicle(vin=OTHER_VIN, purchase_price=10000, asking_price=13000)

    client.post(f"/expenses/vehicle/{on_lot['id']}", json={"category": "Detail", "amount": 200})
    client.post(f"/expenses/vehicle/{sold['id']}", json={"category": "Repair", "amount": 500})
    client.put(f"/vehicles/{sold['id']}/sell", json={"sale_price": 12500})

    body = client.get("/vehicles/dashboard/summary").json()

    assert body["inventory_count"] == 1
    assert body["vehicles_sold"] == 1
    assert body["total_invested"] == 5200
    assert body["inventory_value"] == 8000
    assert body["potential_profit"] == 2800
    assert body["total_sales"] == 12500
    assert body["total_actual_profit"] == 2000


# ---------- VIN decode route ----------

def test_decode_route_returns_vehicle_info(client, monkeypatch):
    monkeypatch.setattr(
        vehicles_router,
        "decode_vin",
        lambda vin: {"vin": vin, "year": "2003", "make": "HONDA", "model": "Accord"},
    )
    response = client.get(f"/vehicles/decode/{VALID_VIN}")
    assert response.status_code == 200
    assert response.json()["make"] == "HONDA"


def test_decode_route_turns_errors_into_400(client, monkeypatch):
    def broken(vin):
        raise ValueError("VIN must contain exactly 17 characters.")

    monkeypatch.setattr(vehicles_router, "decode_vin", broken)
    response = client.get("/vehicles/decode/ABC")
    assert response.status_code == 400
    assert "17 characters" in response.json()["detail"]
