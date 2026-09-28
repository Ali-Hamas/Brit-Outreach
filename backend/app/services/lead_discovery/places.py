"""Google Places business search (v1 core) + Free OpenStreetMap Overpass fallback.

Uses Places Text Search + Place Details endpoints. Returns a list of plain
dicts; never raises to the caller — on failure returns (results, error_message).

Also includes free Overpass API (OpenStreetMap) fallback - NO API KEY NEEDED.
"""
import os
import re
from app.core.config import settings
from app.services.lead_discovery.http_util import request_with_backoff

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

DETAIL_FIELDS = "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total"


OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:25];
(
  node["name"]["shop"~"{industry}"]["addr:city"~"{location}",i](around:50000,0,0);
  way["name"]["shop"~"{industry}"]["addr:city"~"{location}",i](around:50000,0,0);
  node["name"]["amenity"~"{industry}"]["addr:city"~"{location}",i](around:50000,0,0);
  way["name"]["amenity"~"{industry}"]["addr:city"~"{location}",i](around:50000,0,0);
  node["name"]["office"~"{industry}"]["addr:city"~"{location}",i](around:50000,0,0);
  way["name"]["office"~"{industry}"]["addr:city"~"{location}",i](around:50000,0,0);
);
out center tags;
"""


def search_businesses(industry, location, limit=20):
    """Search '<industry> in <location>' and enrich each result with details.

    Returns (leads, error). error is None on success or a human-readable string.
    Tries Google Places first (if key available), falls back to free Overpass API.
    """
    places_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    # Try Google Places first if key available
    if places_key:
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

    # Fallback: Free Overpass API (OpenStreetMap) - NO API KEY NEEDED
    return search_businesses_overpass(industry, location, limit)


def search_businesses_overpass(industry, location, limit=20):
    """Free business search using OpenStreetMap Overpass API - NO API KEY NEEDED."""
    import requests
    
    # Map common industry terms to OSM tags
    industry_map = {
        'dental': ['dentist', 'dental_clinic'],
        'dentist': ['dentist', 'dental_clinic'],
        'law': ['lawyer', 'solicitor', 'legal'],
        'lawyer': ['lawyer', 'solicitor', 'legal'],
        'law firm': ['lawyer', 'solicitor', 'legal'],
        'gym': ['gym', 'fitness_centre', 'fitness_center'],
        'fitness': ['gym', 'fitness_centre', 'fitness_center'],
        'restaurant': ['restaurant', 'cafe', 'fast_food'],
        'cafe': ['cafe', 'restaurant'],
        'coffee': ['cafe', 'coffee_shop'],
        'accounting': ['accountant', 'accountancy'],
        'accountant': ['accountant', 'accountancy'],
        'real estate': ['real_estate', 'estate_agent'],
        'estate agent': ['real_estate', 'estate_agent'],
        'doctor': ['doctor', 'clinic', 'hospital'],
        'clinic': ['clinic', 'hospital', 'doctor'],
        'hospital': ['hospital', 'clinic'],
        'pharmacy': ['pharmacy', 'chemist'],
        'vet': ['veterinary', 'veterinarian'],
        'veterinary': ['veterinary', 'veterinarian'],
        'hair': ['hairdresser', 'beauty_salon'],
        'salon': ['hairdresser', 'beauty_salon'],
        'beauty': ['beauty_salon', 'hairdresser'],
        'spa': ['spa', 'beauty_salon'],
        'hotel': ['hotel', 'hostel', 'guest_house'],
        'hostel': ['hostel', 'hotel'],
        'car': ['car_repair', 'car_dealer', 'car_rental'],
        'auto': ['car_repair', 'car_dealer', 'car_rental'],
        'plumber': ['plumber', 'plumbing'],
        'electrician': ['electrician'],
        'builder': ['construction', 'builder'],
        'architect': ['architect'],
        'marketing': ['marketing', 'advertising_agency'],
        'advertising': ['advertising_agency', 'marketing'],
        'it': ['it', 'software', 'computer'],
        'software': ['software', 'it'],
        'web': ['web_design', 'web_development'],
        'design': ['design', 'graphic_design'],
        'consulting': ['consulting', 'business_consulting'],
        'finance': ['financial_advisor', 'financial_service'],
        'insurance': ['insurance', 'insurance_broker'],
        'bank': ['bank', 'atm'],
    }
    
    # Get OSM tags for industry
    industry_lower = industry.lower().strip()
    osm_tags = industry_map.get(industry_lower, [industry_lower])
    
    # Build Overpass query
    tag_filters = '|'.join(osm_tags)
    query = f"""
    [out:json][timeout:25];
    (
      node["name"]["shop"~"{tag_filters}",i](around:50000,"{location}");
      way["name"]["shop"~"{tag_filters}",i](around:50000,"{location}");
      node["name"]["amenity"~"{tag_filters}",i](around:50000,"{location}");
      way["name"]["amenity"~"{tag_filters}",i](around:50000,"{location}");
      node["name"]["office"~"{tag_filters}",i](around:50000,"{location}");
      way["name"]["office"~"{tag_filters}",i](around:50000,"{location}");
    );
    out center tags;
    """
    
    try:
        resp = requests.post(OVERPASS_URL, data={'data': query}, timeout=30)
        data = resp.json()
        
        leads = []
        for element in data.get('elements', [])[:limit]:
            tags = element.get('tags', {})
            name = tags.get('name', '')
            if not name:
                continue
            
            # Get coordinates
            lat = element.get('lat', element.get('center', {}).get('lat'))
            lon = element.get('lon', element.get('center', {}).get('lon'))
            
            # Build address from tags
            address_parts = []
            for key in ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode', 'addr:country']:
                if key in tags:
                    address_parts.append(tags[key])
            address = ', '.join(address_parts) if address_parts else location
            
            # Phone
            phone = tags.get('phone', tags.get('contact:phone', ''))
            
            # Website
            website = tags.get('website', tags.get('contact:website', ''))
            
            # Rating - not available in OSM
            rating = None
            rating_count = None
            
            leads.append({
                "place_id": f"osm_{element.get('type', '')}_{element.get('id', '')}",
                "business_name": name,
                "address": address,
                "phone": phone,
                "website": website,
                "rating": rating,
                "user_ratings_total": rating_count,
                "industry": industry,
                "location_query": location,
                "source": "OpenStreetMap (free)"
            })
        
        return leads, None
        
    except Exception as e:
        return [], f"Overpass API error: {str(e)}"


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
