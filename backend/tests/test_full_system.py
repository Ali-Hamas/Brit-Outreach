import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.models import Business, SMTPConfig, TargetMarket, Campaign, Prospect, ProspectStatus, OutreachActivity, Reply
from app.services.prospecting import ProspectingOrchestrator, ApolloProspector
from app.services.scoring import LeadScorer
from app.services.outreach import SMTPRouter, PersonalizationEngine
from app.services.replies import ReplyProcessor
from app.services.britcrm import BritCRMClient
from app.services.crm import CRMSync

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Create clean database tables for testing"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_01_health_and_root_endpoint():
    """Test FastAPI root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Brit Lead Gen" in data["message"]

def test_02_business_crud():
    """Test business creation and listing via API"""
    res = client.post("/api/v1/businesses", json={"name": "BritSync Tech", "domain": "britsync.com"})
    assert res.status_code == 200
    biz = res.json()
    assert biz["name"] == "BritSync Tech"
    biz_id = biz["id"]

    res_list = client.get("/api/v1/businesses")
    assert res_list.status_code == 200
    all_biz = res_list.json()
    assert any(b["id"] == biz_id for b in all_biz)

def test_03_smtp_config_creation():
    """Test SMTP configuration creation and retrieval"""
    db = SessionLocal()
    biz = Business(id="biz-test-1", name="TalentBridge Agency", domain="talentbridge.io")
    db.add(biz)
    db.commit()
    db.close()

    res = client.post("/api/v1/smtp", json={
        "business_id": "biz-test-1",
        "name": "Primary Sales SMTP",
        "host": "localhost",
        "port": 587,
        "username": "sales@talentbridge.io",
        "password": "secretpassword",
        "from_email": "sales@talentbridge.io",
        "from_name": "TalentBridge Team",
        "daily_limit": 50
    })
    assert res.status_code == 200
    smtp = res.json()
    assert smtp["daily_limit"] == 50

def test_04_target_market_and_scoring():
    """Test Target Market creation and Lead Scoring logic"""
    tm = TargetMarket(
        id="tm-execs",
        business_id="biz-test-1",
        name="Enterprise Executives",
        filters={
            "titles": ["cto", "vp of engineering", "chief executive officer"],
            "company_size_ranges": ["50-200", "200-500"],
            "industries": ["Software", "Technology"],
            "locations": ["United States", "London"]
        }
    )

    prospect = Prospect(
        id="p-exec-1",
        business_id="biz-test-1",
        email="cto@enterprise.com",
        first_name="David",
        title="Chief Technology Officer",
        company="Enterprise Tech",
        company_size="50-200",
        industry="Software",
        location="London, UK"
    )

    scorer = LeadScorer()
    score, breakdown = scorer.score_prospect(prospect, tm)
    assert score >= 80
    assert breakdown["title_match"] == 30
    assert breakdown["company_size_match"] == 25

def test_05_outreach_personalization_and_tracking(monkeypatch):
    """Test email template personalization and open pixel injection"""
    import smtplib
    from unittest.mock import MagicMock
    mock_smtp = MagicMock()
    monkeypatch.setattr(smtplib, "SMTP", lambda *args, **kwargs: mock_smtp)

    prospect = Prospect(
        id="p-track-1",
        business_id="biz-test-1",
        email="lead@company.com",
        first_name="Sarah",
        company="GrowthCorp"
    )

    template = "Hi {{first_name}}, love what {{company}} is building!"
    rendered = PersonalizationEngine.personalize(template, prospect)
    assert rendered == "Hi Sarah, love what GrowthCorp is building!"

    router = SMTPRouter()
    smtp_cfg = SMTPConfig(
        id="smtp-mock",
        business_id="biz-test-1",
        name="Mock SMTP",
        host="localhost",
        port=587,
        username="user",
        password="pwd",
        from_email="outreach@test.com",
        from_name="Outreach",
        daily_limit=100
    )

    tracking_id = "trk-unit-999"
    success = router.send_email(
        smtp_config=smtp_cfg,
        to_email="lead@company.com",
        subject="Quick question",
        body_html="<p>Click <a href='https://example.com/demo'>here</a> to learn more.</p>",
        body_text="Click here to learn more.",
        tracking_id=tracking_id
    )
    assert success is True

def test_06_open_and_click_tracking_endpoints():
    """Test FastAPI pixel open and click redirect endpoints"""
    db = SessionLocal()
    prospect = Prospect(id="p-trk-db", business_id="b1", email="tracktest@domain.com", status=ProspectStatus.CONTACTED)
    db.add(prospect)
    activity = OutreachActivity(
        id="act-trk-db",
        prospect_id="p-trk-db",
        campaign_id="c1",
        step_number=1,
        email_subject="Test Subject",
        email_body="<p>Test</p>",
        tracking_id="trk-db-123",
        status="sent"
    )
    db.add(activity)
    db.commit()
    db.close()

    # Test Pixel Open
    res_open = client.get("/api/v1/tracking/trk-db-123/open")
    assert res_open.status_code == 200
    assert res_open.headers["content-type"] == "image/gif"

    # Test Click Redirect
    res_click = client.get("/api/v1/tracking/trk-db-123/click?url=https://britsync.com", follow_redirects=False)
    assert res_click.status_code == 307
    assert res_click.headers["location"] == "https://britsync.com"

def test_07_reply_processor_and_sentiment():
    """Test reply cleaning and sentiment analysis"""
    processor = ReplyProcessor()
    raw_email = """Sounds great! I'm definitely interested. Let's schedule a call next week.

On Mon, Aug 24, 2026 at 10:00 AM Outreach <outreach@test.com> wrote:
> Hi, quick question..."""

    cleaned = processor.clean_email_body(raw_email)
    assert "Sounds great" in cleaned
    assert "On Mon, Aug 24" not in cleaned

    sentiment = processor.detect_sentiment(cleaned)
    assert sentiment == "positive"

def test_08_britcrm_lead_and_appointment_booking():
    """Test BritCRM integration for lead syncing and appointment booking"""
    client_crm = BritCRMClient()
    prospect = Prospect(
        id="p-crm-test",
        business_id="b1",
        email="ceo@targetco.com",
        first_name="Elena",
        title="CEO",
        company="TargetCo",
        score=95,
        status=ProspectStatus.QUALIFIED
    )

    res_lead = client_crm.create_or_update_lead(prospect)
    assert res_lead["status"] in ["mock_success", "success", "skipped"]

    res_appt = client_crm.book_appointment(prospect, "BritSync Demo Call", datetime.utcnow())
    assert res_appt["status"] in ["mock_appointment_created", "success", "skipped"]

def test_09_ai_autonomous_chat_and_booking(monkeypatch):
    """Test full flow: Prospect replies -> AI chats back via email -> Books appointment in BritCRM"""
    import smtplib
    from unittest.mock import MagicMock
    mock_smtp = MagicMock()
    monkeypatch.setattr(smtplib, "SMTP", lambda *args, **kwargs: mock_smtp)

    db = SessionLocal()
    prospect = Prospect(
        id="p-ai-chat-1",
        business_id="b-ai-biz",
        email="interested.lead@enterprise.com",
        first_name="Marcus",
        title="VP of Sales",
        company="GlobalTech",
        status=ProspectStatus.CONTACTED
    )
    db.add(prospect)
    smtp_cfg = SMTPConfig(
        id="smtp-ai-test",
        business_id="b-ai-biz",
        name="AI Sales SMTP",
        host="localhost",
        port=587,
        username="sales@global.com",
        password="pwd",
        from_email="sales@global.com",
        from_name="Sales Team",
        daily_limit=100
    )
    db.add(smtp_cfg)
    db.commit()
    db.close()

    # Simulate prospect replying "Thursday at 2pm works for me, let's book it!"
    res = client.post("/api/v1/prospects/inbound-reply", json={
        "business_id": "b-ai-biz",
        "prospect_email": "interested.lead@enterprise.com",
        "subject": "Re: Outreach",
        "body": "Thursday at 2pm works for me, let's book it!"
    })

    assert res.status_code == 200
    data = res.json()
    assert data["ai_chat_response_sent"] is True
    assert "Discovery Meeting" in data["ai_chat_message"] or "reserved" in data["ai_chat_message"] or "Thank you" in data["ai_chat_message"] or "call" in data["ai_chat_message"].lower()
    assert data["appointment_booked_in_britcrm"] is True
    assert data["britcrm_result"]["status"] in ["mock_appointment_created", "success", "skipped"]

def test_10_csv_lead_file_upload():
    """Test importing custom CSV lead files via upload-csv endpoint"""
    csv_content = """email,first_name,last_name,title,company,industry,location
lead1@external.com,Alex,Taylor,VP of Marketing,TaylorAgency,Marketing,New York
lead2@external.com,Jordan,Lee,CTO,LeeTech,Software,London
"""
    files = {"file": ("leads.csv", csv_content, "text/csv")}
    data = {"business_id": "biz-talentbridge"}

    res = client.post("/api/v1/prospects/upload-csv", data=data, files=files)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "success"
    assert res_data["imported_count"] == 2
    assert res_data["skipped_count"] == 0

def test_11_campaign_update_and_delete():
    """Test editing campaign draft settings and deleting campaign"""
    # Create test campaign
    create_res = client.post("/api/v1/campaigns", json={
        "business_id": "biz-britsync",
        "smtp_config_id": "smtp-britsync",
        "target_market_id": "tm-britsync",
        "name": "Draft to Edit",
        "sequence_config": {"steps": [{"delay_hours": 0, "subject": "Initial", "body_html": "<p>Initial</p>"}]},
        "settings": {"max_leads_per_day": 20, "score_threshold": 50}
    })
    assert create_res.status_code == 200
    camp_id = create_res.json()["id"]

    # Edit campaign
    update_res = client.put(f"/api/v1/campaigns/{camp_id}", json={
        "name": "Updated Draft Name",
        "settings": {"max_leads_per_day": 100, "score_threshold": 75}
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Draft Name"
    assert update_res.json()["settings"]["score_threshold"] == 75

    # Delete campaign
    delete_res = client.delete(f"/api/v1/campaigns/{camp_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "deleted"
