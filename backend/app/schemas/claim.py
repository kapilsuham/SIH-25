from pydantic import BaseModel
from typing import Optional

class ClaimBase(BaseModel):
    claimant_name: str
    status: Optional[str] = "Pending"
    area_hectares: float
    geometry: dict  # GeoJSON geometry

class ClaimCreate(ClaimBase):
    pass

class Claim(ClaimBase):
    id: int

    class Config:
        orm_mode = True 