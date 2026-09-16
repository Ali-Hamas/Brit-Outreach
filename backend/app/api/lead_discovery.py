"""Lead Discovery API - finds real prospects using Reddit scraping + web audit. No API keys needed."""
import os
import re
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Business, Prospect, TargetMarket, Campaign

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


def _extract_emails(text: str) -> list[str]:
    return re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)


def _extract_names_from_username(username: str) -> tuple[str, str]:
    parts = username.replace('_', ' ').replace('-', ' ').split()
    if len(parts) >= 2:
        return parts[0].capitalize(), parts[1].capitalize()
    return parts[0].capitalize(), ''


def _guess_email_from_domain(domain: str) -> str:
    return f"info@{domain}"


async def search_reddit_public(keywords: str, limit: int = 25) -> list[dict]:
    """Search Reddit using public JSON endpoint - no API key needed."""
    import httpx

    subreddits = [
        'entrepreneur', 'smallbusiness', 'startups', 'SaaS',
        'webdev', 'ArtificialIntelligence', 'automation',
        'freelance', 'forhire', 'digital_marketing'
    ]

    all_results = []
    search_terms = [keywords.strip()]

    for term in search_terms[:3]:
        for subreddit in subreddits[:5]:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    'q': term,
                    'restrict_sr': 'on',
                    'sort': 'relevance',
                    't': 'month',
                    'limit': str(min(limit, 10))
                }
                headers = {'User-Agent': 'BritOutreach/1.0 (outreach research bot)'}

                async with httpx.AsyncClient(timeout=10) as client:
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
                                'content': p.get('selftext', '')[:500],
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


def _score_lead_from_post(post: dict) -> int:
    score = 50
    content = (post.get('title', '') + ' ' + post.get('content', '')).lower()

    high_intent = ['looking for', 'need help', 'need a', 'recommend', 'anyone know',
                   'suggestion', 'advice', 'hire', 'freelancer', 'agency', 'consultant',
                   'help with', 'struggling with', 'problem with', 'not working']
    for phrase in high_intent:
        if phrase in content:
            score += 15
            break

    medium_intent = ['thinking about', 'considering', 'want to', 'trying to', 'plan to']
    for phrase in medium_intent:
        if phrase in content:
            score += 8
            break

    if post.get('num_comments', 0) > 5:
        score += 5
    if post.get('upvotes', 0) > 10:
        score += 5

    return min(score, 100)


@router.post("/search")
async def search_leads(req: LeadSearchRequest, db: Session = Depends(get_db)):
    """Search for real leads using Reddit scraping. No API keys needed."""
    business = db.query(Business).filter(Business.id == req.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    posts = await search_reddit_public(req.keywords, limit=20)

    leads = []
    seen_emails = set()

    for post in posts:
        author = post.get('author', '')
        if not author or author in ['[deleted]', '[removed]']:
            continue

        emails_in_content = _extract_emails(post.get('content', ''))
        if emails_in_content:
            for email in emails_in_content:
                if email not in seen_emails and 'reddit.com' not in email:
                    seen_emails.add(email)
                    first_name, last_name = _extract_names_from_username(author)
                    leads.append(LeadResult(
                        name=author,
                        email=email,
                        company=f"r/{post.get('subreddit', 'unknown')}",
                        title="Reddit User",
                        source="Reddit",
                        source_url=post.get('url', ''),
                        score=_score_lead_from_post(post),
                        snippet=post.get('title', '')[:200],
                    ))
        else:
            email = f"info@reddit-{author.lower()}.placeholder"
            first_name, last_name = _extract_names_from_username(author)
            leads.append(LeadResult(
                name=author,
                email=email,
                company=f"r/{post.get('subreddit', 'unknown')}",
                title="Reddit User",
                source="Reddit",
                source_url=post.get('url', ''),
                score=_score_lead_from_post(post),
                snippet=post.get('title', '')[:200],
            ))

    leads.sort(key=lambda x: x.score, reverse=True)

    return {
        "status": "success",
        "total_posts": len(posts),
        "leads_found": len(leads),
        "leads": [l.dict() for l in leads[:20]],
        "message": f"Found {len(leads)} potential leads from {len(posts)} Reddit posts"
    }


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
        if not email or '@' not in email or 'placeholder' in email:
            skipped += 1
            continue

        existing = db.query(Prospect).filter(
            Prospect.business_id == business_id,
            Prospect.email == email
        ).first()

        if existing:
            skipped += 1
            continue

        prospect = Prospect(
            business_id=business_id,
            campaign_id=campaign_id,
            email=email,
            first_name=lead.get('name', '').split()[0] if lead.get('name') else '',
            last_name=' '.join(lead.get('name', '').split()[1:]) if lead.get('name') else '',
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
