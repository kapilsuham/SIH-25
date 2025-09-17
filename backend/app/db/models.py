from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geometry
from app.db.session import Base

class FRAClaim(Base):
    __tablename__ = "fra_claims"

    id = Column(Integer, primary_key=True, index=True)
    claimant_name = Column(String, index=True)
    status = Column(String, default="Pending")
    area_hectares = Column(Float)
    geometry = Column(Geometry('POLYGON'))