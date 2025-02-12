from typing import Any, List
from pydantic import BaseModel

from src.multiportal_client.model.dto.identification_dto import IdentificationDto

class VehicleOccupationExpectedOccupationDto(BaseModel):
    comercial_id: str
    occupation: int

class VehicleOccupationDto(BaseModel):
    vehicle_id: int
    plate: str
    capacity: int
    quantity_identifications: int
    identifications: List[IdentificationDto]
    occupation: float
    expected_occupation: float | None = None
    expected_quantity: int| None = None
    travel_time_seconds: int | None = None
    city_zone: str | None = None
    branches: List[str] = []