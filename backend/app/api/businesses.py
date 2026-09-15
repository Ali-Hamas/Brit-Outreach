import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.db.models import Business

router = APIRouter(prefix="/businesses", tags=["Businesses"])

class BusinessCreate(BaseModel):
    name: str
    domain: Optional[str] = None

class BusinessResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str]
    
    class Config:
        from_attributes = True

@router.post("", response_model=BusinessResponse)
def create_business(data: BusinessCreate, db: Session = Depends(get_db)):
    business = Business(id=str(uuid.uuid4()), name=data.name, domain=data.domain)
    db.add(business)
    db.commit()
    db.refresh(business)
    return business

@router.get("", response_model=List[BusinessResponse])
def list_businesses(db: Session = Depends(get_db)):
    return db.query(Business).all()
