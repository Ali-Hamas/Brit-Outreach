"""Influencer Affiliate Outreach API - Find influencers, auto-outreach with 25% commission, track referrals."""
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Business
from app.services.influencer_outreach_agent import InfluencerOutreachAgent

router = APIRouter(prefix="/influencer-outreach", tags=["Influencer Affiliate Outreach"])


class ProductConfig(BaseModel):
    """Product/service configuration for influencer outreach."""
    name: str
    description: str
    website: str
    target_niche: str = "AI & SaaS"
    platforms: List[str] = ["youtube", "instagram", "tiktok", "linkedin"]
    min_followers: int = 1000
    max_influencers: int = 20
    commission_rate: float = 0.25


class InfluencerOutreachRequest(BaseModel):
    business_id: str
    product: ProductConfig
    auto_launch: bool = True


class InfluencerResult(BaseModel):
    name: str
    handle: str
    platform: str
    niche: str
    followers_count: str
    contact_email: str
    profile_url: str
    referral_link: str


@router.post("/find-influencers")
async def find_influencers(req: InfluencerOutreachRequest, db: Session = Depends(get_db)):
    """Find relevant influencers for your product."""
    business = db.query(Business).filter(Business.id == req.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    agent = InfluencerOutreachAgent(business_id=req.business_id)
    
    all_influencers = []
    for platform in req.product.platforms:
        influencers = agent.find_influencers_for_product(
            product_description=req.product.description,
            target_niche=req.product.target_niche,
            platform=platform,
            min_followers=req.product.min_followers,
            max_results=req.product.max_influencers // len(req.product.platforms) + 1
        )
        all_influencers.extend(influencers)
    
    # Deduplicate by email
    seen_emails = set()
    unique_influencers = []
    for inf in all_influencers:
        email = inf.get('contact_email', '')
        if email and email not in seen_emails:
            seen_emails.add(email)
            inf['referral_link'] = f"https://outreach.britsyncai.com/ref/INFL-{email.split('@')[0].upper()[:8]}"
            unique_influencers.append(inf)
    
    return {
        "status": "success",
        "total_found": len(unique_influencers),
        "influencers": unique_influencers[:20],
        "message": f"Found {len(unique_influencers)} influencers with contact emails"
    }


@router.post("/launch-outreach")
async def launch_influencer_outreach(req: InfluencerOutreachRequest, db: Session = Depends(get_db)):
    """Find influencers AND send automated outreach emails with 25% commission."""
    business = db.query(Business).filter(Business.id == req.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    agent = InfluencerOutreachAgent(business_id=req.business_id)
    
    all_influencers = []
    for platform in req.product.platforms:
        influencers = agent.find_influencers_for_product(
            product_description=req.product.description,
            target_niche=req.product.target_niche,
            platform=platform,
            min_followers=req.product.min_followers,
            max_results=req.product.max_influencers // len(req.product.platforms) + 1
        )
        all_influencers.extend(influencers)
    
    # Deduplicate
    seen_emails = set()
    unique_influencers = []
    for inf in all_influencers:
        email = inf.get('contact_email', '')
        if email and email not in seen_emails:
            seen_emails.add(email)
            inf['referral_link'] = f"https://outreach.britsyncai.com/ref/INFL-{email.split('@')[0].upper()[:8]}"
            unique_influencers.append(inf)
    
    if not req.auto_launch:
        return {
            "status": "preview",
            "influencers_found": len(unique_influencers),
            "influencers": unique_influencers[:20],
            "message": "Preview mode - set auto_launch=true to send emails"
        }
    
    # Send outreach
    result = await agent.send_outreach_to_influencers(
        influencers=unique_influencers,
        product_name=req.product.name,
        product_description=req.product.description,
        product_website=req.product.website,
        commission_rate=req.product.commission_rate,
        db=db
    )
    
    return {
        "status": "completed",
        "emails_sent": result["sent"],
        "failed": result["failed"],
        "total_influencers": result["total"],
        "commission_rate": f"{req.product.commission_rate * 100}%",
        "errors": result["errors"][:5]
    }


@router.post("/preview-email")
async def preview_outreach_email(
    influencer_email: str,
    influencer_name: str,
    platform: str,
    product_name: str,
    product_description: str,
    product_website: str,
    commission_rate: float = 0.25
):
    """Preview the outreach email that will be sent."""
    agent = InfluencerOutreachAgent()
    
    influencer = {
        "contact_email": influencer_email,
        "name": influencer_name,
        "platform": platform,
        "niche": "Tech & Business"
    }
    
    email_data = agent.create_outreach_email(
        influencer=influencer,
        product_name=product_name,
        product_description=product_description,
        product_website=product_website,
        commission_rate=commission_rate
    )
    
    return {
        "subject": email_data["subject"],
        "body": email_data["body"],
        "referral_link": email_data["referral_link"]
    }


@router.get("/referral-stats/{ref_code}")
async def get_referral_stats(ref_code: str):
    """Get referral stats for an influencer."""
    from app.services.influencer_outreach_agent import ReferralTracker
    from app.db.session import SessionLocal
    
    tracker = ReferralTracker()
    stats = tracker.get_influencer_stats(ref_code)
    
    return {
        "ref_code": ref_code,
        "stats": stats
    }