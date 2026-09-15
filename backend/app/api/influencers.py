import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.db.session import get_db
from app.db.models import Prospect, ProspectStatus
from app.services.influencer_agent import GroqInfluencerAgent
from app.services.crm import CRMSync
from app.core.config import settings

router = APIRouter(prefix="/influencers", tags=["Influencer Affiliate Agent"])

class InfluencerChatRequest(BaseModel):
    user_query: str
    chat_history: Optional[List[Dict[str, str]]] = []
    groq_api_key: Optional[str] = None

class AddInfluencerRequest(BaseModel):
    business_id: str
    campaign_id: Optional[str] = None
    influencer_name: str
    handle: str
    platform: str
    niche: str
    contact_email: str
    followers_count: Optional[str] = None
    engagement_rate: Optional[str] = None
    affiliate_fit_score: int = 80
    profile_url: Optional[str] = None

@router.post("/chat")
def chat_with_influencer_agent(data: InfluencerChatRequest):
    """Chat endpoint connecting the UI to the Groq AI Influencer Agent"""
    api_key = data.groq_api_key or settings.GROQ_API_KEY
    agent = GroqInfluencerAgent(groq_api_key=api_key)
    result = agent.chat_and_discover(data.user_query, data.chat_history)
    return result

@router.post("/add-to-campaign")
def add_influencer_to_outreach_and_crm(data: AddInfluencerRequest, db: Session = Depends(get_db)):
    """Export a discovered influencer into prospects database and BritCRM for affiliate outreach"""
    email_clean = data.contact_email.lower().strip()

    # Check if prospect exists
    existing = db.query(Prospect).filter(
        Prospect.business_id == data.business_id,
        Prospect.email == email_clean
    ).first()

    if existing:
        prospect = existing
        prospect.score = max(prospect.score, data.affiliate_fit_score)
    else:
        name_parts = data.influencer_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        prospect = Prospect(
            id=str(uuid.uuid4()),
            business_id=data.business_id,
            campaign_id=data.campaign_id,
            email=email_clean,
            first_name=first_name,
            last_name=last_name,
            title=f"Influencer / Creator ({data.platform})",
            company=data.handle,
            industry=data.niche,
            company_size=data.followers_count or "Influencer",
            website=data.profile_url,
            score=data.affiliate_fit_score,
            status=ProspectStatus.NEW,
            source=f"Influencer Agent ({data.platform})"
        )
        db.add(prospect)

    db.commit()
    db.refresh(prospect)

    # Sync to BritCRM
    crm = CRMSync()
    crm_res = crm.sync_prospect(prospect)

    return {
        "status": "added",
        "prospect_id": prospect.id,
        "email": prospect.email,
        "britcrm_synced": True
    }
