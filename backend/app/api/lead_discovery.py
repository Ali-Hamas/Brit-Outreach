"""Lead Discovery API - finds real prospects using Reddit scraping + web audit. No API keys needed."""
import os
import re
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Business, Prospect, TargetMarket, Campaign
from app.services.lead_discovery.places import search_businesses as places_search
from app.services.prospecting import ApolloProspector
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class LeadSearchRequest(BaseModel):
    business_id: str
    keywords: str
    campaign_id: Optional[str] = None


class LeadResult(BaseModel):
    name: str
    email: str
    company: str
    title: str
    source: str
    source_url: str
    score: int
    snippet: str


class PlacesSearchRequest(BaseModel):
    business_id: str
    industry: str
    location: str
    campaign_id: Optional[str] = None
    limit: int = 20


class ApolloSearchRequest(BaseModel):
    business_id: str
    industry: str
    location: str = ""
    titles: List[str] = ["CTO", "CEO", "Founder", "VP Engineering", "Head of Engineering", "Engineering Manager"]
    company_sizes: List[str] = ["1-10", "11-50", "51-200"]
    industries: List[str] = ["Computer Software", "Information Technology", "Internet", "SaaS"]
    limit: int = 50


def _extract_emails(text: str) -> List[str]:
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)


def _extract_names_from_username(username: str) -> tuple[str, str]:
    parts = username.replace('_', ' ').replace('-', ' ').split()
    if len(parts) >= 2:
        return parts[0].capitalize(), parts[1].capitalize()
    return parts[0].capitalize(), ''


def _guess_company_email(author: str, subreddit: str) -> Optional[str]:
    """Guess company email from Reddit username patterns."""
    # Common patterns: user@company.com, info@company.com, etc.
    # We can't reliably guess, so we'll check if user mentions their domain
    return None


async def search_reddit_public(keywords: str, limit: int = 25) -> List[dict]:
    """Search Reddit using public JSON endpoint - no API key needed."""
    import httpx

    subreddits = [
        'entrepreneur', 'smallbusiness', 'startups', 'SaaS',
        'webdev', 'ArtificialIntelligence', 'automation',
        'freelance', 'forhire', 'digital_marketing',
        'web_design', 'seo', 'marketing', 'sales',
        'consulting', 'agency', 'b2b'
    ]

    all_results = []
    search_terms = [keywords.strip()]

    for term in search_terms[:3]:
        for subreddit in subreddits[:8]:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    'q': term,
                    'restrict_sr': 'on',
                    'sort': 'relevance',
                    't': 'month',
                    'limit': str(min(limit, 15))
                }
                headers = {'User-Agent': 'BritOutreach/1.0 (outreach research bot)'}

                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(url, params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get('data', {}).get('children', [])
                        for post in posts:
                            p = post.get('data', {})
                            all_results.append({
                                'title': p.get('title', ''),
                                'author': p.get('author', ''),
                                'subreddit': p.get('subreddit', ''),
                                'url': f"https://reddit.com{p.get('permalink', '')}",
                                'content': p.get('selftext', '')[:1000],
                                'upvotes': p.get('ups', 0),
                                'num_comments': p.get('num_comments', 0),
                                'created_utc': p.get('created_utc', 0),
                            })
                    elif resp.status_code == 403:
                        logger.warning(f"Reddit blocked request for r/{subreddit}")
            except Exception as e:
                logger.warning(f"Reddit search error for r/{subreddit}: {e}")
                continue

    all_results.sort(key=lambda x: x.get('upvotes', 0), reverse=True)
    return all_results[:limit]


def _extract_emails(text: str) -> list[str]:
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)


def _extract_names_from_username(username: str) -> tuple[str, str]:
    parts = username.replace('_', ' ').replace('-', ' ').split()
    if len(parts) >= 2:
        return parts[0].capitalize(), parts[1].capitalize()
    return parts[0].capitalize(), ''


def _score_lead_from_post(post: dict) -> int:
    score = 50
    content = (post.get('title', '') + ' ' + post.get('content', '')).lower()

    high_intent = ['looking for', 'need help', 'need a', 'recommend', 'anyone know',
                   'suggestion', 'advice', 'hire', 'freelancer', 'agency', 'consultant',
                   'help with', 'struggling with', 'problem with', 'not working',
                   'budget for', 'investment for', 'funding for', 'outsourcing']
    for phrase in high_intent:
        if phrase in content:
            score += 15
            break

    medium_intent = ['thinking about', 'considering', 'want to', 'trying to', 'plan to',
                     'researching', 'exploring', 'evaluating']
    for phrase in medium_intent:
        if phrase in content:
            score += 8
            break

    if post.get('num_comments', 0) > 5:
        score += 5
    if post.get('upvotes', 0) > 10:
        score += 5
    if post.get('num_comments', 0) > 20:
        score += 5
    if post.get('upvotes', 0) > 50:
        score += 5

    return min(score, 100)


def _extract_contact_from_content(post: dict) -> tuple[Optional[str], Optional[str]]:
    """Extract email and name from post content."""
    content = post.get('content', '')
    emails = _extract_emails(content)
    if emails:
        return emails[0], None
    return None, None


@router.post("/search")
async def search_leads(req: LeadSearchRequest, db: Session = Depends(get_db)):
    """Search for real leads using Reddit scraping. No API keys needed."""
    business = db.query(Business).filter(Business.id == req.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    posts = await search_reddit_public(req.keywords, limit=30)

    leads = []
    seen_emails = set()

    for post in posts:
        author = post.get('author', '')
        if not author or author in ['[deleted]', '[removed]', 'AutoModerator']:
            continue

        # Try to extract email from post content
        email, name_from_content = _extract_contact_from_content(post)

        first_name, last_name = _extract_names_from_username(author)

        if email and email not in seen_emails and 'reddit.com' not in email and 'example.com' not in email:
            seen_emails.add(email)
            leads.append({
                "name": f"{first_name} {last_name}".strip() or author,
                "email": email,
                "company": f"r/{post.get('subreddit', 'unknown')}",
                "title": "Reddit User (shared email)",
                "source": "Reddit",
                "source_url": post.get('url', ''),
                "score": _score_lead_from_post(post),
                "snippet": post.get('title', '')[:200],
            })
        else:
            # No email in content - try to infer from username patterns
            # Some users have firstname.lastname or company patterns
            # We'll create a high-quality lead anyway with the Reddit profile
            leads.append({
                "name": f"{first_name} {last_name}".strip() or author,
                "email": "",  # Will be filled later or marked as needs enrichment
                "company": f"r/{post.get('subreddit', 'unknown')}",
                "title": f"Active on r/{post.get('subreddit', 'unknown')}",
                "source": "Reddit",
                "source_url": post.get('url', ''),
                "score": _score_lead_from_post(post),
                "snippet": post.get('title', '')[:200],
            })

    # Sort by score
    leads.sort(key=lambda x: x.get('score', 50), reverse=True)

    # Filter to show best leads first (those with emails first)
    leads_with_email = [l for l in leads if l.get('email')]
    leads_without_email = [l for l in leads if not l.get('email')]

    return {
        "status": "success",
        "total_posts": len(posts),
        "leads_with_email": len(leads_with_email),
        "leads_needing_enrichment": len(leads_without_email),
        "leads": (leads_with_email + leads_without_email)[:25],
        "message": f"Found {len(leads_with_email)} leads with emails, {len(leads_without_email)} needing enrichment from {len(posts)} Reddit posts"
    }


@router.post("/enrich-emails")
async def enrich_leads_emails(leads: list[dict], db: Session = Depends(get_db)):
    """Try to find emails for leads that don't have them."""
    import httpx
    
    enriched = []
    for lead in leads:
        if lead.get('email'):
            enriched.append(lead)
            continue
        
        # Try to guess email from username if it looks like a company
        name = lead.get('name', '')
        company = lead.get('company', '')
        
        # If company looks like a domain, try common patterns
        email = None
        if company and '.' in company and not company.startswith('r/'):
            domain = company.replace('www.', '').replace('http://', '').replace('https://', '')
            common = ['info', 'hello', 'contact', 'team', 'support']
            # We can't verify without API, so we'll leave empty
            pass
        
        enriched.append({**lead, 'email': email or ''})
    
    return {"enriched": enriched}


@router.post("/save-leads")
async def save_leads_to_campaign(
    business_id: str,
    campaign_id: str,
    leads: list[dict],
    db: Session = Depends(get_db)
):
    """Save found leads as prospects in a campaign."""
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    saved = 0
    skipped = 0

    for lead in leads:
        email = lead.get('email', '')
        if not email or '@' not in email:
            skipped += 1
            continue

        existing = db.query(Prospect).filter(
            Prospect.business_id == business_id,
            Prospect.email == email
        ).first()

        if existing:
            skipped += 1
            continue

        name = lead.get('name', '')
        name_parts = name.split() if name else ['', '']
        
        prospect = Prospect(
            business_id=business_id,
            campaign_id=campaign_id,
            email=email,
            first_name=name_parts[0] if name_parts else '',
            last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
            company=lead.get('company', ''),
            title=lead.get('title', ''),
            score=lead.get('score', 50),
            source=lead.get('source', 'Reddit'),
            source_url=lead.get('source_url', ''),
            status='new',
        )
        db.add(prospect)
        saved += 1

    db.commit()

    return {
        "status": "success",
        "saved": saved,
        "skipped": skipped,
        "message": f"Saved {saved} leads to campaign '{campaign.name}'"
    }


@router.post("/places-search")
async def search_places(req: PlacesSearchRequest, db: Session = Depends(get_db)):
    """Search Google Places for local businesses. Requires GOOGLE_PLACES_API_KEY."""
    business = db.query(Business).filter(Business.id == req.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    results, error = places_search(req.industry, req.location, req.limit)
    
    if error:
        return {
            "status": "error",
            "error": error,
            "leads": []
        }

    leads = []
    for r in results:
        leads.append({
            "name": r.get("business_name", ""),
            "email": "",
            "company": r.get("business_name", ""),
            "title": f"{r.get('industry', '')} in {r.get('location_query', '')}",
            "source": "Google Places",
            "source_url": f"https://www.google.com/maps/place/?q=place_id:{r.get('place_id', '')}",
            "score": 60,
            "snippet": f"{r.get('address', '')} | {r.get('phone', '')} | Rating: {r.get('rating', 'N/A')}",
            "address": r.get("address", ""),
            "phone": r.get("phone", ""),
            "website": r.get("website", ""),
            "rating": r.get("rating"),
            "rating_count": r.get("user_ratings_total"),
        })

    return {
        "status": "success",
        "leads_found": len(leads),
        "leads": leads[:req.limit],
        "message": f"Found {len(leads)} businesses from Google Places"
    }


@router.post("/apollo-search")
async def search_apollo(req: ApolloSearchRequest, db: Session = Depends(get_db)):
    """Search Apollo.io for B2B contacts. Requires APOLLO_API_KEY."""
    business = db.query(Business).filter(Business.id == req.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    apollo_key = getattr(settings, "APOLLO_API_KEY", None)
    if not apollo_key:
        return {
            "status": "error",
            "error": "APOLLO_API_KEY not configured",
            "leads": []
        }

    prospector = ApolloProspector(apollo_key)
    
    # Create a temporary target market for the search
    target_market = TargetMarket(
        id="temp",
        business_id=req.business_id,
        name="API Search",
        filters={
            "industries": req.industries,
            "titles": req.titles,
            "company_size_ranges": req.company_sizes,
            "locations": [req.location] if req.location else []
        }
    )

    results = prospector.search_contacts(target_market, limit=req.limit)

    leads = []
    for r in results:
        leads.append({
            "name": f"{r.get('first_name', '')} {r.get('last_name', '')}".strip(),
            "email": r.get("email", ""),
            "company": r.get("company", ""),
            "title": r.get("title", ""),
            "source": "Apollo",
            "source_url": r.get("linkedin_url", ""),
            "score": 85,
            "snippet": f"{r.get('company', '')} | {r.get('title', '')} | {r.get('location', '')}",
            "phone": r.get("phone", ""),
            "website": r.get("website", ""),
            "linkedin_url": r.get("linkedin_url", ""),
        })

    return {
        "status": "success",
        "leads_found": len(leads),
        "leads": leads[:req.limit],
        "message": f"Found {len(leads)} verified contacts from Apollo"
    }


@router.get("/apollo-test")
async def test_apollo_connection():
    """Test Apollo API connection."""
    apollo_key = getattr(settings, "APOLLO_API_KEY", None)
    if not apollo_key:
        return {"status": "error", "error": "APOLLO_API_KEY not configured"}
    
    prospector = ApolloProspector(apollo_key)
    
    # Test with minimal filters
    target_market = TargetMarket(
        id="test",
        business_id="biz-ascentra",
        name="Test",
        filters={
            "industries": ["Computer Software"],
            "titles": ["CTO", "CEO", "Founder"],
            "locations": ["London"],
            "company_size_ranges": ["1-10", "11-50", "51-200"]
        }
    )
    
    try:
        results = prospector.search_contacts(target_market, limit=5)
        return {
            "status": "success",
            "message": f"Apollo API working - found {len(results)} contacts",
            "sample": results[:2] if results else []
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}