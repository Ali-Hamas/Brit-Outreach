import uuid
from datetime import datetime, timedelta
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Campaign, Prospect, SMTPConfig, OutreachActivity, CampaignStatus, ProspectStatus
from app.services.outreach import SMTPRouter, PersonalizationEngine

@celery_app.task
def run_daily_followup_sequences():
    """Execute scheduled follow-up sequence steps for active campaigns"""
    db = SessionLocal()
    try:
        active_campaigns = db.query(Campaign).filter(Campaign.status == CampaignStatus.ACTIVE).all()
        smtp_router = SMTPRouter()

        for campaign in active_campaigns:
            steps = (campaign.sequence_config or {}).get("steps", [])
            if not steps:
                continue

            smtp_config = db.query(SMTPConfig).filter(SMTPConfig.id == campaign.smtp_config_id).first()
            if not smtp_config:
                continue

            # Fetch prospects contacted who have not replied or unsubscribed
            eligible_prospects = db.query(Prospect).filter(
                Prospect.campaign_id == campaign.id,
                Prospect.status.in_([ProspectStatus.CONTACTED, ProspectStatus.OPENED, ProspectStatus.CLICKED])
            ).all()

            for prospect in eligible_prospects:
                sent_count = prospect.contact_count or 0
                if sent_count >= len(steps):
                    continue  # Completed sequence

                next_step = steps[sent_count]
                delay_hours = next_step.get("delay_hours", 72)

                # Verify delay time has passed since last email send
                if prospect.last_contacted_at:
                    if datetime.utcnow() < prospect.last_contacted_at + timedelta(hours=delay_hours):
                        continue

                # Execute step
                subject = PersonalizationEngine.personalize(next_step.get("subject", ""), prospect)
                body_html = PersonalizationEngine.personalize(next_step.get("body_html", ""), prospect)
                body_text = PersonalizationEngine.personalize(next_step.get("body_text", ""), prospect)

                tracking_id = str(uuid.uuid4())

                success = smtp_router.send_email(
                    smtp_config=smtp_config,
                    to_email=prospect.email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text,
                    tracking_id=tracking_id
                )

                if success:
                    activity = OutreachActivity(
                        id=str(uuid.uuid4()),
                        prospect_id=prospect.id,
                        campaign_id=campaign.id,
                        step_number=sent_count + 1,
                        email_subject=subject,
                        email_body=body_html,
                        sent_at=datetime.utcnow(),
                        tracking_id=tracking_id,
                        status="sent"
                    )
                    db.add(activity)
                    prospect.contact_count = sent_count + 1
                    prospect.last_contacted_at = datetime.utcnow()
                    prospect.last_email_subject = subject

        db.commit()
    finally:
        db.close()
