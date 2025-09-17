from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.claim import Claim, ClaimCreate
from app.crud import crud_claim

router = APIRouter()

@router.get("/", response_model=List[Claim])
def read_claims(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    claims = crud_claim.get_claims(db, skip=skip, limit=limit)
    return claims

@router.get("/{claim_id}", response_model=Claim)
def read_claim(claim_id: int, db: Session = Depends(get_db)):
    db_claim = crud_claim.get_claim(db, claim_id=claim_id)
    if db_claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return db_claim

@router.post("/", response_model=Claim)
def create_claim(claim: ClaimCreate, db: Session = Depends(get_db)):
    return crud_claim.create_claim(db, claim=claim.dict())