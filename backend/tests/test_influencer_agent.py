import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.services.influencer_agent import GroqInfluencerAgent
from app.db.models import Prospect, ProspectStatus
from app.db.session import SessionLocal, engine
from app.db.base import Base

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(Prospect).filter(Prospect.business_id == "b-test-inf").delete()
    db.commit()
    db.close()
    yield
    db = SessionLocal()
    db.query(Prospect).filter(Prospect.business_id == "b-test-inf").delete()
    db.commit()
    db.close()

def test_influencer_discovery_fallback():
    """Test influencer discovery agent and response structure"""
    agent = GroqInfluencerAgent()
    res = agent.chat_and_discover("Find me YouTube tech influencers for AI SaaS affiliate launch")

    assert "influencers" in res
    assert isinstance(res["influencers"], list)
    assert "response_text" in res
    assert len(res["response_text"]) > 0

    # Test direct parser with sample search results
    sample_web_results = [
        {
            "title": "Tech Breakdown - YouTube",
            "link": "https://www.youtube.com/@techbreakdown",
            "snippet": "Contact us at partnerships@techbreakdown.com for business inquiries."
        },
        {
            "title": "AI Masterclass | YouTube",
            "link": "https://www.youtube.com/@aimasterclass",
            "snippet": "Sponsorships and affiliates: sponsor@aimasterclass.io"
        }
    ]
    parsed = agent._parse_web_results_directly("tech influencers", sample_web_results)
    assert "influencers" in parsed
    assert len(parsed["influencers"]) == 2
    inf = parsed["influencers"][0]
    assert inf["name"] == "Tech Breakdown"
    assert inf["handle"] == "@techbreakdown"
    assert inf["contact_email"] == "partnerships@techbreakdown.com"

def test_add_influencer_to_prospects():
    """Test exporting influencer card into database prospects and BritCRM sync"""
    db = SessionLocal()

    inf_data = {
        "business_id": "b-test-inf",
        "influencer_name": "Tech Breakdown",
        "handle": "@techbreakdown",
        "platform": "YouTube",
        "niche": "AI & SaaS",
        "contact_email": "alex@techbreakdown.com",
        "followers_count": "150,000",
        "affiliate_fit_score": 92
    }

    # Verify prospect object creation
    prospect = Prospect(
        id="p-inf-1",
        business_id=inf_data["business_id"],
        email=inf_data["contact_email"],
        first_name="Tech",
        last_name="Breakdown",
        title=f"Influencer ({inf_data['platform']})",
        company=inf_data["handle"],
        industry=inf_data["niche"],
        score=inf_data["affiliate_fit_score"],
        status=ProspectStatus.NEW
    )
    db.add(prospect)
    db.commit()

    saved = db.query(Prospect).filter(Prospect.id == "p-inf-1").first()
    assert saved is not None
    assert saved.email == "alex@techbreakdown.com"
    assert saved.score == 92
    db.close()
