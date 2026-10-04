import uuid
import requests
import json
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
        
        # Build payload according to Apollo API v1 format
        payload = {
            "api_key": self.api_key,
            "page": 1,
            "per_page": min(limit, 100),
        }
        
        # Add person titles if provided
        titles = filters.get("titles", [])
        if titles:
            payload["person_titles"] = titles
        
        # Add locations if provided
        locations = filters.get("locations", [])
        if locations:
            payload["person_locations"] = locations
        
        # Add organization filters
        org_filters = {}
        industries = filters.get("industries", [])
        if industries:
            org_filters["industry_tags"] = industries
        
        company_sizes = filters.get("company_size_ranges", [])
        if company_sizes:
            org_filters["num_employees_ranges"] = company_sizes
        
        domains = filters.get("domains", [])
        if domains:
            org_filters["domains"] = domains
        
        if org_filters:
            payload["organization"] = org_filters
        
        # Email status
        payload["contact_email_status"] = ["verified"]

        try:
            response = requests.post(
                f"{self.base_url}/mixed_people/search",
                json=payload,
                headers={"Content-Type": "application/json", "Cache-Control": "no-cache"},
                timeout=30
            )
            
            # Log the response for debugging
            if response.status_code != 200:
                print(f"[Prospecting] Apollo API error {response.status_code}: {response.text}")
            
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
