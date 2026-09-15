import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.db.models import SMTPConfig

router = APIRouter(prefix="/smtp", tags=["SMTP Configs"])

class SMTPCreate(BaseModel):
    business_id: str
    name: str
    host: str
    port: int = 587
    username: str
    password: str
    from_email: str
    from_name: str
    daily_limit: int = 100

class SMTPResponse(BaseModel):
    id: str
    business_id: str
    name: str
    host: str
    port: int
    from_email: str
    from_name: str
    daily_limit: int
    is_active: bool

    class Config:
        from_attributes = True

@router.post("", response_model=SMTPResponse)
def create_smtp_config(data: SMTPCreate, db: Session = Depends(get_db)):
    smtp = SMTPConfig(
        id=str(uuid.uuid4()),
        business_id=data.business_id,
        name=data.name,
        host=data.host,
        port=data.port,
        username=data.username,
        password=data.password,
        from_email=data.from_email,
        from_name=data.from_name,
        daily_limit=data.daily_limit
    )
    db.add(smtp)
    db.commit()
    db.refresh(smtp)
    return smtp

@router.get("", response_model=List[SMTPResponse])
@router.get("/all", response_model=List[SMTPResponse])
def get_all_smtps(db: Session = Depends(get_db)):
    return db.query(SMTPConfig).all()

@router.get("/business/{business_id}", response_model=List[SMTPResponse])
def get_business_smtps(business_id: str, db: Session = Depends(get_db)):
    return db.query(SMTPConfig).filter(SMTPConfig.business_id == business_id).all()
