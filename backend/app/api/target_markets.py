import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.db.models import TargetMarket

router = APIRouter(prefix="/target-markets", tags=["Target Markets"])

class TargetMarketCreate(BaseModel):
    business_id: str
    name: str
    filters: Dict[str, Any]
    exclusion_filters: Optional[Dict[str, Any]] = {}

class TargetMarketResponse(BaseModel):
    id: str
    business_id: str
    name: str
    filters: Dict[str, Any]
    exclusion_filters: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

@router.post("", response_model=TargetMarketResponse)
def create_target_market(data: TargetMarketCreate, db: Session = Depends(get_db)):
    tm = TargetMarket(
        id=str(uuid.uuid4()),
        business_id=data.business_id,
        name=data.name,
        filters=data.filters,
        exclusion_filters=data.exclusion_filters
    )
    db.add(tm)
    db.commit()
    db.refresh(tm)
    return tm

@router.get("/business/{business_id}", response_model=List[TargetMarketResponse])
def list_target_markets(business_id: str, db: Session = Depends(get_db)):
    return db.query(TargetMarket).filter(TargetMarket.business_id == business_id).all()
