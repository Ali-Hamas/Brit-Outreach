"""Google Places business search (v1 core).

Uses the Places Text Search + Place Details endpoints. Returns a list of plain
dicts; never raises to the caller — on failure returns (results, error_message).
"""
import os
from app.core.config import settings
from app.services.lead_discovery.http_util import request_with_backoff

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

DETAIL_FIELDS = "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total"


def search_businesses(industry, location, limit=20):
    """Search '<industry> in <location>' and enrich each result with details.

    Returns (leads, error). error is None on success or a human-readable string.
    """
    places_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not places_key:
        return [], "Google Places API key not configured. Set GOOGLE_PLACES_API_KEY environment variable."

    query = f"{industry} in {location}".strip()
    try:
        resp = request_with_backoff(
            "GET",
            TEXT_SEARCH_URL,
            params={"query": query, "key": places_key},
        )
        data = resp.json()
    except Exception as exc:
        return [], f"Places search failed: {exc}"

    status = data.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        return [], f"Places API error: {status} {data.get('error_message', '')}".strip()

    leads = []
    for item in data.get("results", [])[:limit]:
        place_id = item.get("place_id")
        detail = _fetch_details(place_id, places_key) if place_id else {}
        leads.append(
            {
                "place_id": place_id,
                "business_name": detail.get("name") or item.get("name"),
                "address": detail.get("formatted_address") or item.get("formatted_address"),
                "phone": detail.get("formatted_phone_number"),
                "website": detail.get("website"),
                "rating": detail.get("rating") or item.get("rating"),
                "user_ratings_total": detail.get("user_ratings_total")
                or item.get("user_ratings_total"),
                "industry": industry,
                "location_query": location,
            }
        )
    return leads, None


def _fetch_details(place_id, api_key):
    try:
        resp = request_with_backoff(
            "GET",
            DETAILS_URL,
            params={
                "place_id": place_id,
                "fields": DETAIL_FIELDS,
                "key": api_key,
            },
        )
        data = resp.json()
        if data.get("status") == "OK":
            return data.get("result", {})
    except Exception:
        pass
    return {}
