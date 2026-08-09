"""
vin_service.py

Handles VIN decoding for the Dealer Management System.
It connects to the NHTSA vehicle database and automatically retrieves
vehicle information such as year, make, model, trim, and body type.
"""

import requests


# NHTSA Vehicle Product Information Catalog API
NHTSA_API_URL = (
    "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/"
)


def decode_vin(vin: str):
    """
    Decode a 17-character VIN and return useful vehicle information.
    """

    # Clean up the VIN
    vin = vin.strip().upper()

    # Validate VIN length
    if len(vin) != 17:
        raise ValueError(
            "VIN must contain exactly 17 characters."
        )

    # VINs cannot contain I, O, or Q
    if any(character in vin for character in ["I", "O", "Q"]):
        raise ValueError(
            "VIN contains an invalid character."
        )

    # Build the NHTSA API request
    url = f"{NHTSA_API_URL}{vin}?format=json"

    try:
        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise ValueError(
            "Unable to connect to the VIN decoding service."
        ) from error

    # Convert API response to Python data
    data = response.json()

    results = data.get("Results")

    if not results:
        raise ValueError(
            "No vehicle information was found for this VIN."
        )

    vehicle = results[0]

    # Check if NHTSA reported a major decoding error
    error_code = vehicle.get("ErrorCode", "")

    if error_code and error_code != "0":
        error_text = vehicle.get(
            "ErrorText",
            "VIN could not be decoded."
        )

        raise ValueError(error_text)

    # Return only the information our dealership system needs
    return {
        "vin": vin,
        "year": vehicle.get("ModelYear") or None,
        "make": vehicle.get("Make") or None,
        "model": vehicle.get("Model") or None,
        "trim": vehicle.get("Trim") or None,
        "body_type": vehicle.get("BodyClass") or None,
        "fuel_type": vehicle.get("FuelTypePrimary") or None,
        "manufacturer": vehicle.get("Manufacturer") or None,
        "engine_cylinders": vehicle.get("EngineCylinders") or None,
        "engine_displacement": vehicle.get("DisplacementL") or None,
        "drive_type": vehicle.get("DriveType") or None,
        "transmission": vehicle.get("TransmissionStyle") or None,
        "doors": vehicle.get("Doors") or None
    }
