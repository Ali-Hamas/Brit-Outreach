"""Referral tracking API - handles click tracking, conversion tracking, and influencer stats."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db, SessionLocal
from app.db.models import ReferralClick, Commission, Campaign
from app.core.config import settings

router = APIRouter(prefix="/referral", tags=["Referral Tracking"])


@router.get("/click/{ref_code}")
async def track_referral_click(
    ref_code: str,
    request: Request,
    campaign_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Track a referral link click - redirects to the destination."""
    click = ReferralClick(
        ref_code=ref_code,
        influencer_email="",  # Will be populated from ref_code mapping
        campaign_id=campaign_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer")
    )
    db.add(click)
    db.commit()
    
    # Redirect to the actual destination
    destination = f"{settings.BASE_TRACKING_URL}/partner-call"
    return RedirectResponse(url=destination)


@router.post("/conversion")
async def track_conversion(
    ref_code: str,
    amount: float,
    customer_email: str,
    campaign_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Track a conversion and calculate commission."""
    commission_rate = 0.25
    commission_amount = amount * 0.25
    
    commission = Commission(
        ref_code=ref_code,
        influencer_email="",  # Will be populated from ref_code mapping
        campaign_id=campaign_id,
        customer_email=customer_email,
        amount=amount,
        commission_rate=0.25,
        commission_amount=commission_amount,
        status="pending"
    )
    db.add(commission)
    db.commit()
    
    return {
        "status": "success",
        "commission_amount": commission_amount,
        "message": "Conversion tracked successfully"
    }


@router.get("/stats/{ref_code}")
async def get_referral_stats(ref_code: str, db: Session = Depends(get_db)):
    """Get referral stats for an influencer."""
    clicks = db.query(func.count(ReferralClick.id)).filter(ReferralClick.ref_code == ref_code).scalar()
    conversions = db.query(func.count(Commission.id)).filter(Commission.ref_code == ref_code).scalar()
    total_revenue = db.query(func.sum(Commission.amount)).filter(Commission.ref_code == ref_code).scalar() or 0
    total_commission = db.query(func.sum(Commission.commission_amount)).filter(Commission.ref_code == ref_code).scalar() or 0
    pending_commission = db.query(func.sum(Commission.commission_amount)).filter(
        Commission.ref_code == ref_code, Commission.status == "pending"
    ).scalar() or 0
    
    return {
        "ref_code": ref_code,
        "clicks": clicks or 0,
        "conversions": conversions or 0,
        "total_revenue": float(total_revenue),
        "commission_earned": float(total_commission),
        "pending_payout": float(pending_commission)
    }


@router.get("/influencer/{influencer_email}")
async def get_influencer_stats(influencer_email: str, db: Session = Depends(get_db)):
    """Get all referral stats for an influencer."""
    # Get all ref_codes for this influencer (in real implementation, map email to ref_codes)
    # For now, return empty stats
    return {
        "influencer_email": influencer_email,
        "clicks": 0,
        "conversions": 0,
        "total_revenue": 0.0,
        "commission_earned": 0.0,
        "pending_payout": 0.0
    }