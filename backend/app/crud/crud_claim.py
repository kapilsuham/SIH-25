from sqlalchemy.orm import Session
from shapely.geometry import shape
from app.db.models import FRAClaim

def get_claim(db: Session, claim_id: int):
    return db.query(FRAClaim).filter(FRAClaim.id == claim_id).first()

def get_claims(db: Session, skip: int = 0, limit: int = 100):
    return db.query(FRAClaim).offset(skip).limit(limit).all()

def create_claim(db: Session, claim: dict):
    # Convert GeoJSON geometry to WKT
    geo_json_geom = claim["geometry"]
    geom_wkt = shape(geo_json_geom).wkt
    claim_data = {**claim, "geometry": geom_wkt}
    db_claim = FRAClaim(**claim_data)
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim