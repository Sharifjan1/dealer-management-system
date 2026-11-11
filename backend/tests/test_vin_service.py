"""
Tests for app/services/vin_service.py.

The real NHTSA website is never called here. A fake response stands
in for it, so these tests run offline and always give the same result.
"""

import pytest
import requests

from app.services import vin_service

VALID_VIN = "1HGCM82633A004352"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def nhtsa_result(**fields):
    base = {
        "ErrorCode": "0",
        "ModelYear": "2003",
        "Make": "HONDA",
        "Model": "Accord",
        "Trim": "EX",
        "BodyClass": "Coupe",
        "FuelTypePrimary": "Gasoline",
    }
    base.update(fields)
    return {"Results": [base]}


def test_decode_returns_vehicle_details(monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return FakeResponse(nhtsa_result())

    monkeypatch.setattr(vin_service.requests, "get", fake_get)

    info = vin_service.decode_vin(VALID_VIN)

    assert info["vin"] == VALID_VIN
    assert info["year"] == "2003"
    assert info["make"] == "HONDA"
    assert info["model"] == "Accord"
    assert info["body_type"] == "Coupe"
    assert VALID_VIN in calls[0]


def test_decode_cleans_up_lowercase_and_spaces(monkeypatch):
    monkeypatch.setattr(vin_service.requests, "get", lambda url, timeout: FakeResponse(nhtsa_result()))
    info = vin_service.decode_vin("  1hgcm82633a004352 ")
    assert info["vin"] == VALID_VIN


def test_empty_fields_become_none(monkeypatch):
    monkeypatch.setattr(
        vin_service.requests, "get", lambda url, timeout: FakeResponse(nhtsa_result(Trim=""))
    )
    assert vin_service.decode_vin(VALID_VIN)["trim"] is None


@pytest.mark.parametrize("bad_vin", ["", "1HGCM826", "1HGCM82633A0043521"])
def test_wrong_length_vin_is_rejected(bad_vin):
    with pytest.raises(ValueError, match="17 characters"):
        vin_service.decode_vin(bad_vin)


@pytest.mark.parametrize("letter", ["I", "O", "Q"])
def test_vin_with_i_o_or_q_is_rejected(letter):
    vin = letter + VALID_VIN[1:]
    with pytest.raises(ValueError, match="invalid character"):
        vin_service.decode_vin(vin)


def test_network_failure_gives_clear_error(monkeypatch):
    def fail(url, timeout):
        raise requests.ConnectionError("no internet")

    monkeypatch.setattr(vin_service.requests, "get", fail)
    with pytest.raises(ValueError, match="Unable to connect"):
        vin_service.decode_vin(VALID_VIN)


def test_nhtsa_error_code_is_reported(monkeypatch):
    payload = nhtsa_result(ErrorCode="8", ErrorText="No detailed data available")
    monkeypatch.setattr(vin_service.requests, "get", lambda url, timeout: FakeResponse(payload))
    with pytest.raises(ValueError, match="No detailed data"):
        vin_service.decode_vin(VALID_VIN)


def test_empty_results_are_reported(monkeypatch):
    monkeypatch.setattr(vin_service.requests, "get", lambda url, timeout: FakeResponse({"Results": []}))
    with pytest.raises(ValueError, match="No vehicle information"):
        vin_service.decode_vin(VALID_VIN)
