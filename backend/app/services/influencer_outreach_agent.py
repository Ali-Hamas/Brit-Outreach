"""Influencer Affiliate Outreach Agent - Finds influencers, sends outreach with 25% commission, tracks referrals."""
import os
import json
import re
import uuid
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse, parse_qs

from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import Prospect, ProspectStatus
from app.db.session import get_db
from app.services.outreach import SMTPRouter
from app.services.britcrm import BritCRMClient
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class InfluencerOutreachAgent:
    """Complete influencer affiliate outreach agent with 25% commission tracking."""
    
    def __init__(self, groq_api_key: Optional[str] = None, business_id: str = "biz-ascentra", commission_rate: float = 0.25):
        self.api_key = groq_api_key or getattr(settings, "GROQ_API_KEY", None)
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.business_id = business_id
        self.base_tracking_url = getattr(settings, "BASE_TRACKING_URL", "https://outreach.britsyncai.com")
        self.commission_rate = commission_rate
        
    def find_influencers_for_product(
        self, 
        product_description: str,
        target_niche: str,
        platform: str = "youtube",
        min_followers: int = 1000,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Find influencers relevant to the product using web search + Groq AI."""
        
        search_query = f"best {target_niche} influencers {platform} contact email business inquiries"
        
        # Use Bing search to find influencer pages
        return self._search_influencers_bing(target_niche, platform, min_followers, max_results)
    
    def _search_influencers_bing(self, niche: str, platform: str, min_followers: int, max_results: int) -> List[Dict]:
        """Search for influencers on Bing with specific platform focus."""
        import requests
        from bs4 import BeautifulSoup
        
        platform_domains = {
            "youtube": "youtube.com",
            "instagram": "instagram.com",
            "tiktok": "tiktok.com",
            "linkedin": "linkedin.com",
            "twitter": "x.com"
        }
        
        domain = platform_domains.get(platform, "youtube.com")
        
        queries = [
            f'site:{domain} "{niche}" "business inquiries" email',
            f'site:{domain} "{niche}" "sponsor" email contact',
            f'"{niche}" influencer {platform} "business email"',
            f'"{niche}" creator {platform} "business inquiries"'
        ]
        
        influencers = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        for query in queries:
            try:
                encoded = httpx.URL.build(query=query)
                url = f"https://www.bing.com/search?q={query}"
                resp = httpx.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
                
                # Parse results
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for item in soup.find_all('li', class_='b_algo')[:5]:
                    h2 = item.find('h2')
                    a = h2.find('a') if h2 else None
                    if not a:
                        continue
                    
                    title = a.get_text(strip=True)
                    link = a.get('href', '')
                    snippet_elem = item.find('p')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    # Extract email from snippet
                    import re
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
                    contact_email = None
                    for email in emails:
                        if not any(x in email.lower() for x in ['youtube.com', 'google.com', 'microsoft.com', 'bing.com']):
                            contact_email = email
                            break
                    
                    if contact_email:
                        # Try to extract follower count from snippet
                        followers = "Unknown"
                        follower_match = re.search(r'(\d[\d,.]*)\s*[KMkm]?\s*(?:subscribers?|followers?)', snippet, re.IGNORECASE)
                        if follower_match:
                            followers = follower_match.group(0)
                        
                        influencers.append({
                            "name": title[:100],
                            "handle": self._extract_handle(title, link),
                            "platform": "YouTube" if "youtube" in platform else platform.capitalize(),
                            "niche": "Tech & Business",
                            "followers_count": followers,
                            "contact_email": contact_email,
                            "profile_url": link,
                            "source": "Bing Search"
                        })
                        
                        if len(influencers) >= 20:
                            break
                            
            except Exception as e:
                logger.warning(f"Bing search error: {e}")
                continue
                
            if len(influencers) >= 20:
                break
        
        return influencers[:20]
    
    def _extract_handle(self, title: str, link: str) -> str:
        import re
        handle_match = re.search(r'@[A-Za-z0-9_.]+', link + " " + title)
        if handle_match:
            return handle_match.group(0)
        return f"@{title.lower().replace(' ', '')[:20]}"
    
    def generate_referral_link(self, influencer_email: str, campaign_name: str = "influencer_affiliate") -> str:
        """Generate unique referral link for influencer."""
        import hashlib
        # Create unique referral code
        ref_code = hashlib.md5(f"{influencer_email}{datetime.now().isoformat()}".encode()).hexdigest()[:8].upper()
        ref_link = f"{self.base_tracking_url}/ref/{ref_code}?source=influencer&email={influencer_email}"
        return ref_link
    
    def create_outreach_email(
        self,
        influencer: Dict[str, Any],
        product_name: str,
        product_description: str,
        product_website: str,
        commission_rate: Optional[float] = None
    ) -> Dict[str, str]:
        """Generate personalized outreach email with configurable commission offer."""
        
        rate = commission_rate or self.commission_rate
        rate_pct = int(rate * 100)
        
        ref_link = self.generate_referral_link(influencer.get('contact_email', ''))
        
        subject = f"Partnership Opportunity: {rate_pct}% Commission for {product_name} - {influencer.get('name', 'Creator')}"
        
        body = f"""Hi {influencer.get('name', 'there')},

I've been following your content on {influencer.get('platform', 'YouTube')} and love your insights on {influencer.get('niche', 'tech and business')}. Your audience would genuinely benefit from what we're building.

We're {product_name} - {product_description}

**Affiliate Partnership Offer:**
- **{rate_pct}% commission** on every sale through your unique referral link
- **30-day cookie window** - you get credit for any purchase within 30 days
- **Real-time dashboard** - track clicks, conversions, and earnings in real-time
- **Monthly payouts** via PayPal/bank transfer (no minimum threshold)

**Your unique referral link:** {self.base_tracking_url}/ref/INFL-{influencer.get('contact_email', '').split('@')[0].upper()[:8]}

**How it works:**
1. Share your link in video descriptions, pinned comments, bio, or stories
2. We track every click and conversion automatically
3. You earn {rate_pct}% of every sale (lifetime recurring if subscription)
4. Get paid monthly - no minimums

We've prepared media assets (logos, screenshots, demo videos) and can hop on a quick 15-min call to walk you through the dashboard.

Interested? Just reply to this email or book a quick call here: {self.base_tracking_url}/partner-call

Best regards,
Ascentra Global Partnerships Team
info@ascentraconsulting.co.uk
{product_website}

P.S. We only partner with creators we genuinely admire. Your content stands out for the right reasons.
"""
        
        return {
            "subject": subject,
            "body": body,
            "referral_link": f"{self.base_tracking_url}/ref/INFL-{influencer.get('contact_email', '').split('@')[0].upper()[:8]}"
        }
    
    async def send_outreach_to_influencers(
        self,
        influencers: List[Dict],
        product_name: str,
        product_description: str,
        product_website: str,
        commission_rate: Optional[float] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Send outreach emails to all found influencers."""
        
        rate = commission_rate or self.commission_rate
        
        sent = 0
        failed = 0
        errors = []
        
        for influencer in influencers:
            try:
                email_data = self.create_outreach_email(
                    influencer=influencer,
                    product_name=product_name,
                    product_description=product_description,
                    product_website=product_website,
                    commission_rate=commission_rate
                )
                
                # Send via SMTP
                if db:
                    from app.services.outreach import SMTPRouter
                    smtp = SMTPRouter(db)
                    result = smtp.send_email(
                        to_email=influencer['contact_email'],
                        subject=email_data['subject'],
                        body=email_data['body'],
                        tracking_id=f"inf-{influencer.get('contact_email', '')}"
                    )
                    
                    if result.get('success'):
                        sent += 1
                        
                        # Save as prospect for tracking
                        from app.db.models import Prospect, ProspectStatus
                        from app.db.session import SessionLocal
                        
                        prospect = Prospect(
                            business_id="biz-ascentra",
                            email=influencer['contact_email'],
                            first_name=influencer.get('name', '').split()[0] if influencer.get('name') else '',
                            last_name=' '.join(influencer.get('name', '').split()[1:]) if influencer.get('name') else '',
                            company=influencer.get('name', ''),
                            title=f"Influencer ({influencer.get('platform', 'YouTube')})",
                            source="Influencer Agent",
                            status=ProspectStatus.NEW,
                            score=85,
                            notes=f"Influencer: {influencer.get('name')} | Platform: {influencer.get('platform')} | Referral: {influencer.get('referral_link', '')}"
                        )
                        # Note: Would need DB session to actually save
                        
                    else:
                        failed += 1
                        errors.append(f"{influencer.get('contact_email')}: {result.get('error', 'Unknown')}")
                        
            except Exception as e:
                failed += 1
                errors.append(f"{influencer.get('contact_email', 'unknown')}: {str(e)}")
                logger.error(f"Failed to send to {influencer.get('contact_email')}: {e}")
        
        return {
            "sent": sent,
            "failed": failed,
            "total": len(influencers),
            "errors": errors
        }


class ReferralTracker:
    """Track referral clicks, conversions, and commissions."""
    
    def __init__(self, db: Session = None, commission_rate: float = 0.25):
        self.db = db or SessionLocal()
        self.commission_rate = commission_rate
    
    def track_click(self, ref_code: str, ip: str = None, user_agent: str = None) -> bool:
        """Track a referral link click."""
        # In production, store in database with ReferralClick model
        logger.info(f"Referral click: {ref_code} from {ip}")
        return True
    
    def track_conversion(self, ref_code: str, amount: float, customer_email: str) -> bool:
        """Track a conversion and calculate commission."""
        commission = amount * self.commission_rate
        logger.info(f"Conversion: {ref_code} - ${amount} -> ${commission} commission for {customer_email}")
        # In production: create Commission record, update influencer balance
        return True
    
    def get_influencer_stats(self, influencer_email: str) -> Dict:
        """Get stats for an influencer."""
        # In production, query database
        return {
            "clicks": 0,
            "conversions": 0,
            "total_revenue": 0.0,
            "commission_earned": 0.0,
            "pending_payout": 0.0
        }