import base64
from datetime import datetime
from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import OutreachActivity, Prospect, ProspectStatus

router = APIRouter(prefix="/tracking", tags=["Tracking"])

# 1x1 Transparent GIF pixel
TRACKING_PIXEL_GIF = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

@router.get("/{tracking_id}/open")
def track_email_open(tracking_id: str, db: Session = Depends(get_db)):
    """Record open event when recipient's email client loads the 1x1 pixel image"""
    activity = db.query(OutreachActivity).filter(OutreachActivity.tracking_id == tracking_id).first()
    if activity:
        if not activity.opened_at:
            activity.opened_at = datetime.utcnow()
            activity.status = "opened"
            
            prospect = db.query(Prospect).filter(Prospect.id == activity.prospect_id).first()
            if prospect:
                prospect.email_opens = (prospect.email_opens or 0) + 1
                if prospect.status not in [ProspectStatus.REPLIED, ProspectStatus.QUALIFIED, ProspectStatus.MEETING_BOOKED]:
                    prospect.status = ProspectStatus.OPENED
            db.commit()

    return Response(content=TRACKING_PIXEL_GIF, media_type="image/gif")


@router.get("/{tracking_id}/click")
def track_link_click(tracking_id: str, url: str, db: Session = Depends(get_db)):
    """Record click event and redirect user to target URL"""
    activity = db.query(OutreachActivity).filter(OutreachActivity.tracking_id == tracking_id).first()
    if activity:
        if not activity.clicked_at:
            activity.clicked_at = datetime.utcnow()
            activity.status = "clicked"

            prospect = db.query(Prospect).filter(Prospect.id == activity.prospect_id).first()
            if prospect:
                prospect.email_clicks = (prospect.email_clicks or 0) + 1
                if prospect.status not in [ProspectStatus.REPLIED, ProspectStatus.QUALIFIED, ProspectStatus.MEETING_BOOKED]:
                    prospect.status = ProspectStatus.CLICKED
            db.commit()

    return RedirectResponse(url=url)
