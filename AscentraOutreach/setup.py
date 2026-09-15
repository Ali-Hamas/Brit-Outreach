"""One-click setup for all campaigns.

Just run: python setup.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault("DATABASE_URL", "sqlite:///./brit_outreach.db")

from app.db.session import SessionLocal, engine
from app.db.models import Business, SMTPConfig, TargetMarket, Campaign
from app.db.base import Base

Base.metadata.create_all(bind=engine)

with open(os.path.join(os.path.dirname(__file__), 'config', 'campaigns.json')) as f:
    config = json.load(f)

db = SessionLocal()

try:
    # Create business
    biz = db.query(Business).first()
    if not biz:
        biz = Business(name=config["company_name"], domain=config["website"])
        db.add(biz)
        db.commit()
        db.refresh(biz)
        print(f"Created business: {config['company_name']}")
    else:
        print(f"Business exists: {biz.name}")

    # Create single SMTP
    smtp = db.query(SMTPConfig).filter(SMTPConfig.from_email == config["smtp"]["email"]).first()
    if not smtp:
        smtp = SMTPConfig(
            business_id=biz.id,
            name="Main SMTP",
            host=config["smtp"]["host"],
            port=config["smtp"]["port"],
            username=config["smtp"]["email"],
            password=config["smtp"]["password"],
            from_email=config["smtp"]["email"],
            from_name=config["smtp"]["from_name"],
            daily_limit=400,
            is_active=True
        )
        db.add(smtp)
        db.commit()
        db.refresh(smtp)
        print(f"Created SMTP: {config['smtp']['email']}")
    else:
        print(f"SMTP exists: {smtp.from_email}")

    # Create campaigns
    for camp in config["campaigns"]:
        existing = db.query(Campaign).filter(Campaign.name == camp["name"]).first()
        if not existing:
            # Create target market
            tm = TargetMarket(
                business_id=biz.id,
                name=f"{camp['name']} Target",
                filters={"industries": ["Technology", "Software", "Healthcare", "Finance"]}
            )
            db.add(tm)
            db.commit()
            db.refresh(tm)

            # Create campaign
            campaign = Campaign(
                business_id=biz.id,
                smtp_config_id=smtp.id,
                target_market_id=tm.id,
                name=camp["name"],
                status="draft",
                sequence_config={
                    "steps": [{
                        "delay_hours": 0,
                        "subject": camp["subject"],
                        "body_html": camp["body"].replace("\n", "<br>"),
                        "body_text": camp["body"]
                    }]
                },
                settings={"max_leads_per_day": camp["daily_limit"], "score_threshold": 60}
            )
            db.add(campaign)
            db.commit()
            print(f"Created campaign: {camp['name']}")
        else:
            print(f"Campaign exists: {camp['name']}")

    print("\n=== SETUP COMPLETE ===")
    print(f"Email: {config['smtp']['email']}")
    print(f"Campaigns: {len(config['campaigns'])}")
    print("\nNext steps:")
    print("  1. cd backend")
    print("  2. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("  3. cd ../frontend && npm run dev")
    print("  4. Open http://localhost:3000")

finally:
    db.close()
