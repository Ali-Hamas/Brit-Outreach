"""Seed all 4 Ascentra Global campaigns into Brit Outreach System.

Run this once to set up:
  cd "M:\Brit Outreach System\backend"
  python ../AscentraOutreach/seed_ascentra.py
"""
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

os.environ.setdefault("DATABASE_URL", "sqlite:///./brit_outreach.db")

from app.db.session import SessionLocal
from app.db.models import Business, SMTPConfig, TargetMarket, Campaign
from app.db.base import Base
from app.db.session import engine

# Create tables
Base.metadata.create_all(bind=engine)

# Load config
config_path = os.path.join(os.path.dirname(__file__), 'config', 'campaigns.json')
with open(config_path) as f:
    config = json.load(f)

db = SessionLocal()

try:
    # 1. Create business
    biz_name = config["company"]["name"]
    biz = db.query(Business).filter(Business.name == biz_name).first()
    if not biz:
        biz = Business(name=biz_name, domain=config["company"]["website"])
        db.add(biz)
        db.commit()
        db.refresh(biz)
        print(f"[OK] Created business: {biz_name} (id={biz.id})")
    else:
        print(f"[SKIP] Business exists: {biz_name} (id={biz.id})")

    # 2. Create SMTP accounts
    smtp_ids = {}
    for smtp_cfg in config["smtp_accounts"]:
        existing = db.query(SMTPConfig).filter(
            SMTPConfig.business_id == biz.id,
            SMTPConfig.from_email == smtp_cfg["from_email"]
        ).first()
        if not existing:
            smtp = SMTPConfig(
                business_id=biz.id,
                name=smtp_cfg["name"],
                host=smtp_cfg["host"],
                port=smtp_cfg["port"],
                username=smtp_cfg["username"],
                password=smtp_cfg["password"],
                from_email=smtp_cfg["from_email"],
                from_name=smtp_cfg["from_name"],
                daily_limit=smtp_cfg["daily_limit"],
                is_active=True
            )
            db.add(smtp)
            db.commit()
            db.refresh(smtp)
            smtp_ids[smtp_cfg["campaign"]] = smtp.id
            print(f"[OK] Created SMTP: {smtp_cfg['name']} ({smtp_cfg['from_email']})")
        else:
            smtp_ids[smtp_cfg["campaign"]] = existing.id
            print(f"[SKIP] SMTP exists: {smtp_cfg['from_email']}")

    # 3. Create target markets and campaigns
    for camp_cfg in config["campaigns"]:
        # Create target market
        tm_name = camp_cfg["target_market"]["name"]
        tm = db.query(TargetMarket).filter(
            TargetMarket.business_id == biz.id,
            TargetMarket.name == tm_name
        ).first()
        if not tm:
            tm = TargetMarket(
                business_id=biz.id,
                name=tm_name,
                filters=camp_cfg["target_market"]["filters"]
            )
            db.add(tm)
            db.commit()
            db.refresh(tm)
            print(f"[OK] Created target market: {tm_name}")
        else:
            print(f"[SKIP] Target market exists: {tm_name}")

        # Determine SMTP ID
        smtp_email = camp_cfg["smtp_email"]
        smtp_id = None
        for s_id, s in db.query(SMTPConfig.id, SMTPConfig.from_email).filter(
            SMTPConfig.business_id == biz.id
        ).all():
            if s == smtp_email:
                smtp_id = s_id
                break

        if not smtp_id:
            smtp_id = list(smtp_ids.values())[0]

        # Create campaign
        existing_camp = db.query(Campaign).filter(
            Campaign.business_id == biz.id,
            Campaign.name == camp_cfg["name"]
        ).first()
        if not existing_camp:
            campaign = Campaign(
                business_id=biz.id,
                smtp_config_id=smtp_id,
                target_market_id=tm.id,
                name=camp_cfg["name"],
                status="draft",
                sequence_config={
                    "steps": [{
                        "delay_hours": 0,
                        "subject": camp_cfg["email_templates"]["subject"],
                        "body_html": camp_cfg["email_templates"]["body"].replace("\n", "<br>"),
                        "body_text": camp_cfg["email_templates"]["body"]
                    }]
                },
                settings=camp_cfg["settings"]
            )
            db.add(campaign)
            db.commit()
            print(f"[OK] Created campaign: {camp_cfg['name']}")
        else:
            print(f"[SKIP] Campaign exists: {camp_cfg['name']}")

    print("\n" + "=" * 60)
    print("ASCENTRA GLOBAL CAMPAIGNS SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nBusiness: {biz_name}")
    print(f"SMTP Accounts: {len(config['smtp_accounts'])}")
    print(f"Campaigns: {len(config['campaigns'])}")
    print(f"\nEmail Templates Ready:")
    for c in config["campaigns"]:
        print(f"  - {c['name']}: {c['smtp_email']}")
    print(f"\nRun the system:")
    print(f"  cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

finally:
    db.close()
