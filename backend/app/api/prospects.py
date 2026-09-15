import csv
import io
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.session import get_db
from app.db.models import Prospect, ProspectStatus, Reply, SMTPConfig, Campaign, TargetMarket
from app.services.replies import ReplyProcessor
from app.services.ai_responder import AIConversationResponder
from app.services.scoring import LeadScorer
from app.services.crm import CRMSync

router = APIRouter(prefix="/prospects", tags=["Prospects"])

class ProspectResponse(BaseModel):
    id: str
    business_id: str
    campaign_id: Optional[str]
    email: str
    phone: Optional[str] = None
    first_name: Optional[str]
    last_name: Optional[str]
    title: Optional[str]
    company: Optional[str]
    company_size: Optional[str]
    industry: Optional[str]
    location: Optional[str]
    linkedin_url: Optional[str]
    score: int
    score_breakdown: Optional[Dict[str, Any]]
    status: ProspectStatus
    contact_count: int
    last_contacted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ProspectCreate(BaseModel):
    business_id: str
    email: str
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    campaign_id: Optional[str] = None

class InboundReplyCreate(BaseModel):
    prospect_email: str
    business_id: str
    subject: Optional[str] = None
    body: str

@router.post("", response_model=ProspectResponse)
def create_single_prospect(data: ProspectCreate, db: Session = Depends(get_db)):
    """Add a single prospect directly into the database and sync to CRM"""
    email_clean = data.email.lower().strip()
    existing = db.query(Prospect).filter(
        Prospect.business_id == data.business_id,
        Prospect.email == email_clean
    ).first()

    if existing:
        if data.phone and not existing.phone:
            existing.phone = data.phone
        if data.campaign_id:
            existing.campaign_id = data.campaign_id
        db.commit()
        db.refresh(existing)
        return existing

    prospect = Prospect(
        id=str(uuid.uuid4()),
        business_id=data.business_id,
        campaign_id=data.campaign_id,
        email=email_clean,
        phone=data.phone,
        first_name=data.first_name,
        last_name=data.last_name,
        title=data.title,
        company=data.company,
        industry=data.industry,
        location=data.location,
        score=90,
        status=ProspectStatus.NEW,
        source="Manual Quick Add"
    )
    db.add(prospect)
    db.commit()
    db.refresh(prospect)

    crm = CRMSync()
    crm.sync_prospect(prospect)
    return prospect

@router.post("/upload-csv")
def upload_prospects_csv(
    business_id: str = Form(...),
    campaign_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload CSV lead file, parse contacts, score against target market, and upsert leads into pipeline & BritCRM"""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV format (.csv)")

    try:
        content = file.file.read().decode("utf-8-sig", errors="ignore")
        reader = csv.DictReader(io.StringIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed parsing CSV file: {str(e)}")

    scorer = LeadScorer()
    crm = CRMSync()

    # Fetch target market if campaign specified
    target_market = None
    if campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            target_market = db.query(TargetMarket).filter(TargetMarket.id == campaign.target_market_id).first()

    imported_prospects = []
    skipped_count = 0

    for row in reader:
        # Standardize header matching (case insensitive)
        clean_row = {str(k).lower().strip().replace(" ", "_"): v for k, v in row.items() if k}
        
        email = clean_row.get("email") or clean_row.get("email_address") or clean_row.get("contact_email")
        if not email or "@" not in str(email):
            skipped_count += 1
            continue

        email = str(email).lower().strip()

        first_name = clean_row.get("first_name") or clean_row.get("firstname") or clean_row.get("first") or ""
        last_name = clean_row.get("last_name") or clean_row.get("lastname") or clean_row.get("last") or ""
        title = clean_row.get("title") or clean_row.get("job_title") or clean_row.get("position") or ""
        company = clean_row.get("company") or clean_row.get("company_name font-medium") or clean_row.get("organization") or ""
        industry = clean_row.get("industry") or clean_row.get("category") or ""
        location = clean_row.get("location") or clean_row.get("city") or clean_row.get("country") or ""
        company_size = clean_row.get("company_size") or clean_row.get("employees font-medium") or clean_row.get("size") or ""
        linkedin_url = clean_row.get("linkedin_url") or clean_row.get("linkedin") or ""
        website = clean_row.get("website font-medium") or clean_row.get("url") or ""
        phone = clean_row.get("phone") or clean_row.get("telephone") or clean_row.get("mobile") or clean_row.get("phone_number") or clean_row.get("tel") or None

        # Check existing prospect
        existing = db.query(Prospect).filter(
            Prospect.business_id == business_id,
            Prospect.email == email
        ).first()

        if existing:
            if campaign_id:
                existing.campaign_id = campaign_id
            if phone and not existing.phone:
                existing.phone = phone
            prospect = existing
        else:
            prospect = Prospect(
                id=str(uuid.uuid4()),
                business_id=business_id,
                campaign_id=campaign_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                title=title,
                company=company,
                industry=industry,
                location=location,
                company_size=company_size,
                linkedin_url=linkedin_url,
                website=website,
                phone=phone,
                source="CSV Upload",
                status=ProspectStatus.NEW
            )
            db.add(prospect)

        # Score prospect and ensure default qualified score (85) for CSV uploaded leads
        if target_market:
            score, breakdown = scorer.score_prospect(prospect, target_market)
            prospect.score = max(score, 85)
            prospect.score_breakdown = breakdown
        else:
            prospect.score = 85

        imported_prospects.append(prospect)
        crm.sync_prospect(prospect)

    db.commit()

    return {
        "status": "success",
        "imported_count": len(imported_prospects),
        "skipped_count": skipped_count,
        "filename": file.filename
    }

@router.get("", response_model=List[ProspectResponse])
def list_prospects(
    business_id: Optional[str] = None,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Prospect)
    if business_id:
        query = query.filter(Prospect.business_id == business_id)
    if status:
        query = query.filter(Prospect.status == status)
    if min_score is not None:
        query = query.filter(Prospect.score >= min_score)
    return query.order_by(Prospect.score.desc()).all()

@router.get("/business/{business_id}", response_model=List[ProspectResponse])
def get_prospects_by_business(
    business_id: str,
    status: Optional[str] = None,
    min_score: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Prospect).filter(Prospect.business_id == business_id)
    if status:
        query = query.filter(Prospect.status == status)
    if min_score is not None:
        query = query.filter(Prospect.score >= min_score)
    return query.order_by(Prospect.score.desc()).all()

@router.post("/inbound-reply")
def handle_inbound_reply(data: InboundReplyCreate, db: Session = Depends(get_db)):
    """Inbound email reply handler: parses reply, triggers AI conversational chat, and books appointment in BritCRM"""
    prospect = db.query(Prospect).filter(
        Prospect.business_id == data.business_id,
        Prospect.email == data.prospect_email.lower().strip()
    ).first()

    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect email not found for this business")

    # 1. Process and record reply
    processor = ReplyProcessor()
    reply = processor.process_inbound_reply(prospect, data.body, subject=data.subject)
    db.add(reply)
    db.commit()

    # 2. Get SMTP Config for business to reply back
    smtp_config = db.query(SMTPConfig).filter(SMTPConfig.business_id == data.business_id).first()
    if not smtp_config:
        raise HTTPException(status_code=400, detail="No SMTP config found for this business. Configure SMTP first.")

    # 3. Autonomous AI Conversation Chat & BritCRM Booking
    ai_responder = AIConversationResponder()
    chat_res = ai_responder.process_and_auto_chat(prospect, reply.content, smtp_config)
    db.commit()

    return {
        "status": "processed",
        "prospect_status": prospect.status.value,
        "sentiment": reply.sentiment,
        "ai_chat_response_sent": chat_res["email_sent_to_prospect"],
        "ai_chat_message": chat_res["ai_chat_response"],
        "appointment_booked_in_britcrm": chat_res["appointment_booked_in_britcrm"],
        "britcrm_result": chat_res["britcrm_result"]
    }
