import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.models import Business, SMTPConfig, TargetMarket, Campaign, CampaignStatus

def ensure_seeded():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        count = db.query(Business).count()
        smtp_count = db.query(SMTPConfig).count()
        if count < 1 or smtp_count < 1:
            db.close()
            seed_database()
        else:
            db.close()
    except Exception:
        db.close()
        seed_database()

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing seed data completely
    try:
        db.query(Campaign).delete()
        db.query(TargetMarket).delete()
        db.query(SMTPConfig).delete()
        db.query(Business).delete()
        db.commit()
    except Exception:
        db.rollback()

    # Read SMTP credentials from environment variables
    smtp_host = os.environ.get("SMTP_HOST", "live.noblecircle.online")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_email = os.environ.get("SMTP_EMAIL", "info@ascentraconsulting.co.uk")
    smtp_password = os.environ.get("SMTP_PASSWORD", "Uk2023@walse")
    smtp_from_name = os.environ.get("SMTP_FROM_NAME", "Ascentra Global")

    company_name = os.environ.get("COMPANY_NAME", "Ascentra Global Ltd")
    company_domain = os.environ.get("COMPANY_DOMAIN", "ascentraconsulting.co.uk")

    print(f"[Seed Data] Seeding primary SMTP account '{smtp_email}' for {company_name}...")

    # 1. Single Primary SMTP Configuration for ALL Outreach
    primary_smtp = SMTPConfig(
        id="smtp-ascentra-primary",
        business_id="biz-ascentra",
        name=f"Ascentra Primary ({smtp_email})",
        host=smtp_host,
        port=smtp_port,
        username=smtp_email,
        password=smtp_password,
        from_email=smtp_email,
        from_name=smtp_from_name,
        daily_limit=500
    )
    db.add(primary_smtp)

    # 2. Main Business: Ascentra Global Ltd
    biz_main = Business(id="biz-ascentra", name=company_name, domain=company_domain)
    db.add(biz_main)

    # 3. Target Markets for the 4 Campaigns
    tm_ai = TargetMarket(
        id="tm-ai-consultancy",
        business_id="biz-ascentra",
        name="UK/US Tech Startups & Enterprises (AI Strategy)",
        filters={"industries": ["FinTech", "HealthTech", "SaaS", "E-commerce"], "titles": ["CEO", "CTO", "VP Engineering"]}
    )
    tm_talent = TargetMarket(
        id="tm-talentbridge",
        business_id="biz-ascentra",
        name="UK/US Hiring Orgs (Remote AI & Tech Engineers)",
        filters={"industries": ["Software", "AI", "Tech"], "titles": ["CTO", "VP Engineering", "Head of Engineering"]}
    )
    tm_biometric = TargetMarket(
        id="tm-biometric",
        business_id="biz-ascentra",
        name="EU & UK Apps & Public Sector (Passwordless)",
        filters={"industries": ["Mobile Apps", "Public Sector", "Security"], "titles": ["CISO", "Product Lead", "CTO"]}
    )
    tm_sentrivault = TargetMarket(
        id="tm-sentrivault",
        business_id="biz-ascentra",
        name="NHS Vendors & Regulated Suppliers (DTAC/DSPT)",
        filters={"industries": ["HealthTech", "NHS Suppliers", "MedTech"], "titles": ["Founder", "CEO", "CTO", "Compliance Lead"]}
    )
    db.add_all([tm_ai, tm_talent, tm_biometric, tm_sentrivault])

    # 4. The 4 Ascentra Campaigns (All using info@ascentraconsulting.co.uk)
    campaigns = [
        Campaign(
            id="camp-ai-consultancy",
            business_id="biz-ascentra",
            smtp_config_id="smtp-ascentra-primary",
            target_market_id="tm-ai-consultancy",
            name="AI Consultancy — AI & Business Transformation",
            status=CampaignStatus.ACTIVE,
            sequence_config={
                "steps": [{
                    "delay_hours": 0,
                    "subject": "AI roadmap for {{company}}",
                    "body_html": "<p>Hi {{first_name}},</p><p>Is {{company}} sitting on data but without a clear AI roadmap to cut costs and drive growth?</p><p>We at Ascentra Global Ltd help leadership teams drive business transformation through AI.</p><p>Best regards,<br><b>Ascentra Global Team</b><br>info@ascentraconsulting.co.uk</p>",
                    "body_text": "Hi {{first_name}}, Is {{company}} sitting on data but without a clear AI roadmap to cut costs and drive growth? We at Ascentra Global Ltd help leadership teams drive business transformation through AI. Best regards, Ascentra Global Team (info@ascentraconsulting.co.uk)"
                }]
            },
            settings={"max_leads_per_day": 100, "score_threshold": 60}
        ),
        Campaign(
            id="camp-talentbridge",
            business_id="biz-ascentra",
            smtp_config_id="smtp-ascentra-primary",
            target_market_id="tm-talentbridge",
            name="TalentBridge — AI & Tech Talent Provision",
            status=CampaignStatus.ACTIVE,
            sequence_config={
                "steps": [{
                    "delay_hours": 0,
                    "subject": "Engineers for {{company}} in 2 weeks",
                    "body_html": "<p>Hi {{first_name}},</p><p>Need tech talent at {{company}} without the usual 3-month hiring delay? We lease pre-vetted remote AI/tech engineers placed within 2 weeks.</p><p>Best regards,<br><b>TalentBridge (Ascentra Global)</b><br>info@ascentraconsulting.co.uk</p>",
                    "body_text": "Hi {{first_name}}, Need tech talent at {{company}} without the usual 3-month hiring delay? We lease pre-vetted remote AI/tech engineers placed within 2 weeks. Best regards, TalentBridge (info@ascentraconsulting.co.uk)"
                }]
            },
            settings={"max_leads_per_day": 200, "score_threshold": 60}
        ),
        Campaign(
            id="camp-biometric",
            business_id="biz-ascentra",
            smtp_config_id="smtp-ascentra-primary",
            target_market_id="tm-biometric",
            name="Biometric Sign Up — Passwordless Technology",
            status=CampaignStatus.ACTIVE,
            sequence_config={
                "steps": [{
                    "delay_hours": 0,
                    "subject": "Passwordless sign-up for {{company}}",
                    "body_html": "<p>Hi {{first_name}},</p><p>Our Biometric Sign Up technology lets users sign up with biometric only—like 'Sign up with Google'—generating a unique single-device ID.</p><p>Best regards,<br><b>Ascentra Global Team</b><br>info@ascentraconsulting.co.uk</p>",
                    "body_text": "Hi {{first_name}}, Our Biometric Sign Up technology lets users sign up with biometric only. Best regards, Ascentra Global Team (info@ascentraconsulting.co.uk)"
                }]
            },
            settings={"max_leads_per_day": 50, "score_threshold": 60}
        ),
        Campaign(
            id="camp-sentrivault",
            business_id="biz-ascentra",
            smtp_config_id="smtp-ascentra-primary",
            target_market_id="tm-sentrivault",
            name="Sentrivault — NHS & Enterprise Compliance Vault",
            status=CampaignStatus.ACTIVE,
            sequence_config={
                "steps": [{
                    "delay_hours": 0,
                    "subject": "DTAC/DSPT ready for {{company}} in 30 days",
                    "body_html": "<p>Hi {{first_name}},</p><p>Is {{company}}'s NHS contract stalled waiting for DTAC or DSPT? We provide the biometric authentication + encrypted vault compliance pack that makes NHS vendors audit-ready in 30 days.</p><p>Best regards,<br><b>Sentrivault (Ascentra Global)</b><br>info@ascentraconsulting.co.uk</p>",
                    "body_text": "Hi {{first_name}}, Is {{company}}'s NHS contract stalled waiting for DTAC or DSPT? We make NHS vendors audit-ready in 30 days. Best regards, Sentrivault (info@ascentraconsulting.co.uk)"
                }]
            },
            settings={"max_leads_per_day": 50, "score_threshold": 60}
        )
    ]
    db.add_all(campaigns)

    db.commit()
    db.close()
    print(f"[Seed Data] Seeding complete! Ascentra Global Ltd & 4 Campaigns configured with primary SMTP.")

if __name__ == "__main__":
    seed_database()
