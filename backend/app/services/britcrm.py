import requests
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.db.models import Prospect

class BritCRMClient:
    """Integration client for BritCRM (https://truecrm.online/api/mcp)"""

    def __init__(self, bearer_token: Optional[str] = None, base_url: Optional[str] = None):
        self.base_url = base_url or getattr(settings, "BRITCRM_API_URL", "https://truecrm.online/api/mcp")
        self.bearer_token = bearer_token or getattr(settings, "BRITCRM_BEARER_TOKEN", None)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        return headers

    def _is_configured(self) -> bool:
        """Check if BritCRM is properly configured with a real token."""
        return bool(self.bearer_token and self.bearer_token.strip() and self.bearer_token != "your_britcrm_token_here")

    def create_or_update_lead(self, prospect: Prospect) -> Dict[str, Any]:
        """Push discovered or qualified lead directly to BritCRM Leads table."""
        if not self._is_configured():
            return {"status": "skipped", "reason": "BritCRM not configured", "email": prospect.email}

        payload = {
            "jsonrpc": "2.0",
            "method": "leads/upsert",
            "params": {
                "email": prospect.email,
                "first_name": prospect.first_name or "",
                "last_name": prospect.last_name or "",
                "title": prospect.title or "",
                "company": prospect.company or "",
                "industry": prospect.industry or "",
                "location": prospect.location or "",
                "linkedin_url": prospect.linkedin_url or "",
                "score": prospect.score,
                "status": prospect.status.value if hasattr(prospect.status, "value") else str(prospect.status),
                "source": prospect.source or "Outreach Engine"
            },
            "id": 1
        }

        try:
            res = requests.post(self.base_url, json=payload, headers=self._get_headers(), timeout=10)
            if res.status_code in [200, 201]:
                data = res.json()
                data["status"] = "success"
                return data
            else:
                return {"status": "error", "email": prospect.email, "http_code": res.status_code, "detail": res.text[:200]}
        except Exception as e:
            return {"status": "error", "email": prospect.email, "message": str(e)}

    def book_appointment(
        self,
        prospect: Prospect,
        title: str,
        start_time: datetime,
        duration_minutes: int = 30,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Book a calendar meeting / call directly in BritCRM."""
        if not self._is_configured():
            return {"status": "skipped", "reason": "BritCRM not configured", "lead": prospect.email}

        payload = {
            "jsonrpc": "2.0",
            "method": "meetings/create",
            "params": {
                "lead_email": prospect.email,
                "title": title,
                "start_time": start_time.isoformat(),
                "duration_minutes": duration_minutes,
                "notes": notes or f"Automated booking for qualified lead {prospect.email} (Score: {prospect.score})"
            },
            "id": 2
        }

        try:
            res = requests.post(self.base_url, json=payload, headers=self._get_headers(), timeout=10)
            if res.status_code in [200, 201]:
                data = res.json()
                data["status"] = "success"
                return data
            else:
                return {"status": "error", "lead": prospect.email, "http_code": res.status_code, "detail": res.text[:200]}
        except Exception as e:
            return {"status": "error", "lead": prospect.email, "message": str(e)}
