import requests
from typing import Optional
from app.db.models import Prospect
from app.services.britcrm import BritCRMClient

class CRMSync:
    """Syncs prospect state and outreach logs with BritCRM, HubSpot, or internal database"""

    def __init__(self, hubspot_api_key: Optional[str] = None):
        self.hubspot_api_key = hubspot_api_key
        self.britcrm = BritCRMClient()

    def sync_prospect(self, prospect: Prospect) -> bool:
        """Sync prospect info to BritCRM and external CRM"""
        # Always sync to BritCRM
        self.britcrm.create_or_update_lead(prospect)

        if self.hubspot_api_key:
            return self._sync_to_hubspot(prospect)
        else:
            print(f"[CRM Sync Internal] Prospect {prospect.email} synced to BritCRM with status: {prospect.status}")
            return True

    def book_appointment_in_crm(self, prospect: Prospect, title: str, start_time, notes: Optional[str] = None):
        """Create appointment in BritCRM calendar"""
        return self.britcrm.book_appointment(prospect, title, start_time, notes=notes)

    def _sync_to_hubspot(self, prospect: Prospect) -> bool:
        """Post contact creation or update to HubSpot CRM API"""
        url = "https://api.hubapi.com/crm/v3/objects/contacts"
        headers = {
            "Authorization": f"Bearer {self.hubspot_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "properties": {
                "email": prospect.email,
                "firstname": prospect.first_name or "",
                "lastname": prospect.last_name or "",
                "jobtitle": prospect.title or "",
                "company": prospect.company or "",
                "city": prospect.location or "",
                "lifecyclestage": "lead"
            }
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            return res.status_code in [200, 201]
        except Exception as e:
            print(f"[CRM Sync Error] HubSpot API failed: {e}")
            return False
