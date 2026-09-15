from typing import Dict, Any, List, Tuple
from app.db.models import Prospect, TargetMarket, ProspectStatus

class LeadScorer:
    """ICP Fit Lead Scorer"""

    def __init__(self):
        self.weights = {
            "title_match": 30,
            "company_size_match": 25,
            "industry_match": 25,
            "location_match": 10,
            "technology_match": 10
        }

    def score_prospect(self, prospect: Prospect, target_market: TargetMarket) -> Tuple[int, Dict[str, Any]]:
        """Score a prospect (0-100) against target market criteria"""
        score = 0
        breakdown = {}
        filters = target_market.filters or {}

        # 1. Job Title Match
        target_titles = [t.lower().strip() for t in filters.get("titles", [])]
        if prospect.title and target_titles:
            p_title = prospect.title.lower()
            # Acronym map for common executive titles
            acronyms = {
                "cto": "chief technology officer",
                "ceo": "chief executive officer",
                "cfo": "chief financial officer",
                "coo": "chief operating officer",
                "cmo": "chief marketing officer",
                "cro": "chief revenue officer",
                "vp": "vice president"
            }
            expanded_targets = []
            for t in target_titles:
                expanded_targets.append(t)
                if t in acronyms:
                    expanded_targets.append(acronyms[t])

            if any(t in p_title or p_title in t for t in expanded_targets):
                score += self.weights["title_match"]
                breakdown["title_match"] = self.weights["title_match"]
            else:
                breakdown["title_match"] = 0
        else:
            breakdown["title_match"] = 0

        # 2. Company Size Match
        size_ranges = filters.get("company_size_ranges", [])
        if prospect.company_size and size_ranges:
            if any(str(r) in str(prospect.company_size) for r in size_ranges):
                score += self.weights["company_size_match"]
                breakdown["company_size_match"] = self.weights["company_size_match"]
            else:
                breakdown["company_size_match"] = 0
        else:
            breakdown["company_size_match"] = self.weights["company_size_match"] if not size_ranges else 0

        # 3. Industry Match
        target_industries = [i.lower().strip() for i in filters.get("industries", [])]
        if prospect.industry and target_industries:
            if any(ind in prospect.industry.lower() for ind in target_industries):
                score += self.weights["industry_match"]
                breakdown["industry_match"] = self.weights["industry_match"]
            else:
                breakdown["industry_match"] = 0
        else:
            breakdown["industry_match"] = self.weights["industry_match"] if not target_industries else 0

        # 4. Location Match
        target_locations = [l.lower().strip() for l in filters.get("locations", [])]
        if prospect.location and target_locations:
            if any(loc in prospect.location.lower() for loc in target_locations):
                score += self.weights["location_match"]
                breakdown["location_match"] = self.weights["location_match"]
            else:
                breakdown["location_match"] = 0
        else:
            breakdown["location_match"] = self.weights["location_match"] if not target_locations else 0

        # 5. Technology Match
        target_techs = [tc.lower().strip() for tc in filters.get("technologies", [])]
        raw_techs = [str(tc).lower() for tc in (prospect.raw_data or {}).get("technologies", [])]
        if target_techs and raw_techs:
            if any(t in raw_techs for t in target_techs):
                score += self.weights["technology_match"]
                breakdown["technology_match"] = self.weights["technology_match"]
            else:
                breakdown["technology_match"] = 0
        else:
            breakdown["technology_match"] = 0

        total_score = min(score, 100)
        return total_score, breakdown

    def score_batch(self, prospects: List[Prospect], target_market: TargetMarket, threshold: int = 60) -> List[Prospect]:
        """Score a list of prospects and update their status if they pass threshold"""
        for prospect in prospects:
            score, breakdown = self.score_prospect(prospect, target_market)
            prospect.score = score
            prospect.score_breakdown = breakdown
            if score >= threshold and prospect.status == ProspectStatus.NEW:
                prospect.status = ProspectStatus.SCORED
        return prospects
