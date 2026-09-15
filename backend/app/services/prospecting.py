import uuid
import requests
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Prospect, TargetMarket, ProspectStatus

class ApolloProspector:
    """Apollo.io integration for lead discovery"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"

    def search_contacts(self, target_market: TargetMarket, limit: int = 100) -> List[Dict[str, Any]]:
        """Search Apollo for contacts matching target market criteria"""
        if not self.api_key:
            return []

        filters = target_market.filters or {}
        payload = {
            "api_key": self.api_key,
            "q_organization_domains": filters.get("domains", []),
            "organization_locations": filters.get("locations", []),
            "person_titles": filters.get("titles", []),
            "organization_num_employees_ranges": filters.get("company_size_ranges", []),
            "organization_industry_tag_ids": filters.get("industries", []),
            "contact_email_status": ["verified"],
            "page": 1,
            "per_page": min(limit, 100)
        }

        try:
            response = requests.post(
                f"{self.base_url}/mixed_people/search",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for person in data.get("people", []):
                email = person.get("email")
                if not email:
                    continue
                results.append({
                    "email": email,
                    "first_name": person.get("first_name"),
                    "last_name": person.get("last_name"),
                    "title": person.get("title"),
                    "company": person.get("organization", {}).get("name"),
                    "company_size": str(person.get("organization", {}).get("estimated_num_employees", "")),
                    "industry": person.get("organization", {}).get("industry"),
                    "location": f"{person.get('city', '')}, {person.get('country', '')}".strip(", "),
                    "linkedin_url": person.get("linkedin_url"),
                    "website": person.get("organization", {}).get("website_url"),
                    "phone": person.get("phone_numbers", [{}])[0].get("raw_number") if person.get("phone_numbers") else None,
                    "raw_data": person,
                    "source": "apollo",
                    "source_id": person.get("id")
                })
            return results
        except Exception as e:
            print(f"[Prospecting] Apollo search error: {e}")
            return []


class ProspectingOrchestrator:
    """Orchestrates multi-source prospecting and database deduplication"""

    def __init__(self, db: Session, apollo_api_key: Optional[str] = None):
        self.db = db
        self.apollo = ApolloProspector(apollo_api_key) if apollo_api_key else None

    def discover_and_save_leads(self, target_market: TargetMarket, campaign_id: Optional[str] = None, limit: int = 50) -> List[Prospect]:
        """Fetch leads from Apollo/sources and upsert to database without duplicate emails per business"""
        found_data = []
        if self.apollo:
            found_data = self.apollo.search_contacts(target_market, limit=limit)

        saved_prospects = []
        for lead in found_data:
            existing = self.db.query(Prospect).filter(
                Prospect.business_id == target_market.business_id,
                Prospect.email == lead["email"].lower().strip()
            ).first()

            if existing:
                # Update existing prospect's campaign_id if requested
                if campaign_id and not existing.campaign_id:
                    existing.campaign_id = campaign_id
                saved_prospects.append(existing)
            else:
                prospect = Prospect(
                    id=str(uuid.uuid4()),
                    business_id=target_market.business_id,
                    campaign_id=campaign_id,
                    email=lead["email"].lower().strip(),
                    first_name=lead.get("first_name"),
                    last_name=lead.get("last_name"),
                    title=lead.get("title"),
                    company=lead.get("company"),
                    company_size=lead.get("company_size"),
                    industry=lead.get("industry"),
                    location=lead.get("location"),
                    linkedin_url=lead.get("linkedin_url"),
                    website=lead.get("website"),
                    phone=lead.get("phone"),
                    raw_data=lead.get("raw_data", {}),
                    source=lead.get("source", "apollo"),
                    source_id=lead.get("source_id"),
                    status=ProspectStatus.NEW
                )
                self.db.add(prospect)
                saved_prospects.append(prospect)

        self.db.commit()
        return saved_prospects
