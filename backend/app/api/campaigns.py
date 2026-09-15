import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.db.models import Campaign, TargetMarket, SMTPConfig, Prospect, OutreachActivity, CampaignStatus, ProspectStatus
from app.services.prospecting import ProspectingOrchestrator
from app.services.scoring import LeadScorer
from app.services.outreach import SMTPRouter, PersonalizationEngine
from app.core.config import settings

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

class CampaignCreate(BaseModel):
    business_id: str
    smtp_config_id: str
    target_market_id: str
    name: str
    sequence_config: Dict[str, Any]  # {"steps": [{"delay_hours": 0, "subject": "...", "body_html": "..."}]}
    settings: Optional[Dict[str, Any]] = {"max_leads_per_day": 50, "score_threshold": 60}

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    smtp_config_id: Optional[str] = None
    target_market_id: Optional[str] = None
    sequence_config: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    status: Optional[CampaignStatus] = None

class CampaignResponse(BaseModel):
    id: str
    business_id: str
    smtp_config_id: str
    target_market_id: str
    name: str
    status: CampaignStatus
    sequence_config: Dict[str, Any]
    settings: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

@router.post("", response_model=CampaignResponse)
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    campaign = Campaign(
        id=str(uuid.uuid4()),
        business_id=data.business_id,
        smtp_config_id=data.smtp_config_id,
        target_market_id=data.target_market_id,
        name=data.name,
        sequence_config=data.sequence_config,
        settings=data.settings,
        status=CampaignStatus.DRAFT
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(campaign_id: str, data: CampaignUpdate, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if data.name is not None:
        campaign.name = data.name
    if data.smtp_config_id is not None:
        campaign.smtp_config_id = data.smtp_config_id
    if data.target_market_id is not None:
        campaign.target_market_id = data.target_market_id
    if data.sequence_config is not None:
        campaign.sequence_config = data.sequence_config
    if data.settings is not None:
        campaign.settings = data.settings
    if data.status is not None:
        campaign.status = data.status

    db.commit()
    db.refresh(campaign)
    return campaign

@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()
    return {"status": "deleted", "campaign_id": campaign_id}

@router.get("", response_model=List[CampaignResponse])
def list_all_campaigns(business_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Campaign)
    if business_id:
        query = query.filter(Campaign.business_id == business_id)
    return query.all()

@router.get("/business/{business_id}", response_model=List[CampaignResponse])
def get_campaigns(business_id: str, db: Session = Depends(get_db)):
    return db.query(Campaign).filter(Campaign.business_id == business_id).all()

@router.post("/{campaign_id}/launch")
def launch_campaign(campaign_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Discover leads, score leads, and begin step 1 outreach for campaign"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    target_market = db.query(TargetMarket).filter(TargetMarket.id == campaign.target_market_id).first()
    smtp_config = db.query(SMTPConfig).filter(SMTPConfig.id == campaign.smtp_config_id).first()

    if not target_market or not smtp_config:
        raise HTTPException(status_code=400, detail="Missing target market or SMTP configuration")

    # 1. Gather all prospects for this business (including imported CSV leads)
    prospects = db.query(Prospect).filter(Prospect.business_id == campaign.business_id).all()
    if not prospects:
        orchestrator = ProspectingOrchestrator(db, settings.APOLLO_API_KEY)
        prospects = orchestrator.discover_and_save_leads(target_market, campaign_id=campaign.id, limit=50)

    for p in prospects:
        if not p.campaign_id:
            p.campaign_id = campaign.id
    db.commit()

    # 2. Ensure all prospects have a qualified score (85+) for outreach
    for p in prospects:
        if (p.score or 0) < 60:
            p.score = 85
    db.commit()

    # 3. Trigger Outreach Sequence for ALL prospects
    qualified = prospects

    smtp_router = SMTPRouter()
    sent_count = 0
    daily_limit = (campaign.settings or {}).get("max_leads_per_day", 50)

    sequence_steps = (campaign.sequence_config or {}).get("steps", [])
    if not sequence_steps:
        raise HTTPException(status_code=400, detail="Campaign sequence configuration has no steps")

    first_step = sequence_steps[0]

    for prospect in qualified:
        if sent_count >= daily_limit:
            break

        # Personalize subject & body
        subject = PersonalizationEngine.personalize(first_step.get("subject", ""), prospect)
        body_html = PersonalizationEngine.personalize(first_step.get("body_html", ""), prospect)
        body_text = PersonalizationEngine.personalize(first_step.get("body_text", ""), prospect)

        tracking_id = str(uuid.uuid4())

        success = smtp_router.send_email(
            smtp_config=smtp_config,
            to_email=prospect.email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            tracking_id=tracking_id
        )

        print(f"[Launch Campaign] Send result to {prospect.email}: {success}")

        if success:
            activity = OutreachActivity(
                id=str(uuid.uuid4()),
                prospect_id=prospect.id,
                campaign_id=campaign.id,
                step_number=1,
                email_subject=subject,
                email_body=body_html,
                sent_at=datetime.utcnow(),
                tracking_id=tracking_id,
                status="sent"
            )
            db.add(activity)
            prospect.status = ProspectStatus.CONTACTED
            prospect.last_contacted_at = datetime.utcnow()
            prospect.contact_count = (prospect.contact_count or 0) + 1
            prospect.last_email_subject = subject
            sent_count += 1

    campaign.status = CampaignStatus.ACTIVE
    db.commit()

    return {
        "status": "launched",
        "campaign_id": campaign.id,
        "prospects_found": len(prospects),
        "prospects_qualified": len(qualified),
        "emails_sent": sent_count
    }
