import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.db.models import Prospect, TargetMarket, SMTPConfig, ProspectStatus
from app.services.scoring import LeadScorer
from app.services.outreach import PersonalizationEngine, SMTPRouter
from app.services.replies import ReplyProcessor

def test_lead_scoring():
    scorer = LeadScorer()
    tm = TargetMarket(
        id="tm1",
        business_id="b1",
        name="Tech Executives",
        filters={
            "titles": ["cto", "vp of engineering"],
            "company_size_ranges": ["50-200"],
            "industries": ["Software", "Technology"],
            "locations": ["United States", "UK"]
        }
    )

    prospect = Prospect(
        id="p1",
        business_id="b1",
        email="cto@techcompany.com",
        first_name="Alice",
        title="Chief Technology Officer",
        company="TechCorp",
        company_size="50-200",
        industry="Software",
        location="London, UK"
    )

    score, breakdown = scorer.score_prospect(prospect, tm)
    assert score >= 80
    assert breakdown["title_match"] == 30
    assert breakdown["company_size_match"] == 25
    assert breakdown["industry_match"] == 25
    assert breakdown["location_match"] == 10

def test_personalization():
    prospect = Prospect(
        id="p1",
        business_id="b1",
        email="john@acme.com",
        first_name="John",
        company="Acme Corp"
    )

    tmpl = "Hi {{first_name}}, quick question regarding {{company}}'s outreach."
    rendered = PersonalizationEngine.personalize(tmpl, prospect)
    assert rendered == "Hi John, quick question regarding Acme Corp's outreach."

def test_reply_processor_sentiment():
    processor = ReplyProcessor()
    body_positive = "Hi, thanks for reaching out. Let's schedule a call next week."
    sentiment = processor.detect_sentiment(body_positive)
    assert sentiment == "positive"

    body_unsubscribe = "Please unsubscribe me from your mailing list immediately."
    sentiment_unsub = processor.detect_sentiment(body_unsubscribe)
    assert sentiment_unsub == "unsubscribe"

def test_smtp_router_mock(monkeypatch):
    import smtplib
    from unittest.mock import MagicMock
    mock_smtp = MagicMock()
    monkeypatch.setattr(smtplib, "SMTP", lambda *args, **kwargs: mock_smtp)

    router = SMTPRouter()
    smtp_config = SMTPConfig(
        id="s1",
        business_id="b1",
        name="Test SMTP",
        host="localhost",
        port=587,
        username="user",
        password="pwd",
        from_email="outreach@test.com",
        from_name="Test Sender",
        daily_limit=10
    )

    success = router.send_email(
        smtp_config=smtp_config,
        to_email="lead@domain.com",
        subject="Hello",
        body_html="<p>Test email</p>",
        body_text="Test email",
        tracking_id="track-123"
    )
    assert success is True

def test_britcrm_integration():
    from app.services.britcrm import BritCRMClient
    client = BritCRMClient()
    prospect = Prospect(
        id="p-brit1",
        business_id="b1",
        email="lead@britcrm.com",
        first_name="Sam",
        title="CEO",
        company="BritCorp",
        score=90,
        status=ProspectStatus.QUALIFIED
    )

    res_lead = client.create_or_update_lead(prospect)
    assert res_lead["status"] in ["mock_success", "success", "skipped"]

    from datetime import datetime
    res_appt = client.book_appointment(prospect, "Discovery Call with Sam", datetime.utcnow())
    assert res_appt["status"] in ["mock_appointment_created", "success", "skipped"]
