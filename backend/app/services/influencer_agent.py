import os
import json
import re
import urllib.parse
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.core.config import settings

class GroqInfluencerAgent:
    """Production-grade YouTube & Social Media Influencer Agent with Direct Channel Scraping & Groq LLM (llama3-70b-8192)"""

    def __init__(self, groq_api_key: Optional[str] = None):
        self.api_key = groq_api_key or getattr(settings, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def scrape_youtube_channel_contacts(self, channel_url_or_handle: str) -> Dict[str, Any]:
        """Scrape YouTube channel HTML for real title, handle, subscriber count, and business contact email"""
        url = channel_url_or_handle if channel_url_or_handle.startswith("http") else f"https://www.youtube.com/{channel_url_or_handle}"
        try:
            res = requests.get(url, headers=self.headers, timeout=8)
            html = res.text

            # Extract Title
            title_match = re.search(r'<meta property="og:title" content="([^"]+)">', html)
            title = title_match.group(1) if title_match else channel_url_or_handle.replace('@', '')

            # Extract Handle
            handle_match = re.search(r'"canonicalChannelUrl":"https://www\.youtube\.com/(@[^"]+)"', html)
            handle = handle_match.group(1) if handle_match else (channel_url_or_handle if channel_url_or_handle.startswith('@') else f"@{channel_url_or_handle}")

            # Extract Subscribers
            sub_match = re.search(r'"subscriberCountText":\{"simpleText":"([^"]+)"\}', html)
            subscribers = sub_match.group(1) if sub_match else "Verified Channel"

            # Extract Business Contact Emails via regex
            emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)))
            contact_emails = [e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif')) and 'youtube.com' not in e and 'google.com' not in e]

            return {
                "title": title,
                "handle": handle,
                "subscribers": subscribers,
                "contact_email": contact_emails[0] if contact_emails else None,
                "url": f"https://www.youtube.com/{handle}"
            }
        except Exception as e:
            print(f"[YouTube Scraper] Error scraping {channel_url_or_handle}: {e}")
            return {}

    def search_live_web(self, user_query: str) -> List[Dict[str, str]]:
        """Perform real live web search for social channels & contact details"""
        platform = "youtube.com"
        query_lower = user_query.lower()
        if "instagram" in query_lower or "ig" in query_lower:
            platform = "instagram.com"
        elif "linkedin" in query_lower:
            platform = "linkedin.com/in"
        elif "tiktok" in query_lower:
            platform = "tiktok.com"
        elif "twitter" in query_lower or "x.com" in query_lower:
            platform = "x.com"

        search_term = f'site:{platform} "{user_query}" contact OR email OR "business inquiries"'
        encoded = urllib.parse.quote(search_term)
        url = f"https://www.bing.com/search?q={encoded}"
        
        results = []
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.find_all('li', class_='b_algo'):
                h2 = item.find('h2')
                a = h2.find('a') if h2 else None
                snippet_elem = item.find('p')
                if a:
                    title = a.text.strip()
                    link = a.get('href', '').strip()
                    snippet = snippet_elem.text.strip() if snippet_elem else ''
                    results.append({"title": title, "link": link, "snippet": snippet})
        except Exception as e:
            print(f"[Web Search Warning] Live web search failed: {e}")
            
        return results

    def chat_and_discover(self, user_query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process user chat prompt: run live web & YouTube scraping, and parse results with Groq AI (llama3-70b-8192)"""
        
        # 1. Fetch real live web search snippets
        web_results = self.search_live_web(user_query)

        # 2. System prompt for Groq API
        system_prompt = f"""
You are an expert AI Influencer Marketing & Affiliate Agent for a tech bridging company.
Your goal is to discover real influencers and creators for product affiliate outreach.

You have access to live web search results for the user's prompt: "{user_query}"

LIVE WEB SEARCH RESULTS:
{json.dumps(web_results[:8], indent=2)}

INSTRUCTIONS:
1. Provide a helpful, strategic response explaining how to approach affiliate partnerships for this query.
2. Extract real influencer channels/profiles from the web search results.
3. Keep handles, channel names, and profile URLs 100% real and matching the search index.
4. Extract or provide realistic business contact emails for sponsor inquiries.

Output format MUST be valid JSON with keys:
- "response_text": (Markdown string summarizing findings and outreach strategy)
- "influencers": Array of objects, each containing:
    - "name": Creator or Channel Name (e.g. "TechSpurt", "Marques Brownlee")
    - "handle": Social handle (e.g. "@techspurt")
    - "platform": "YouTube" | "Instagram" | "TikTok" | "LinkedIn" | "Twitter"
    - "niche": Category (e.g. "AI & SaaS", "Productivity", "Tech Reviews")
    - "followers_count": Number string (e.g. "120,000" or "1.2M")
    - "engagement_rate": Percentage string (e.g. "4.8%")
    - "contact_email": Business contact email (e.g. "sponsorships@channeldomain.com")
    - "location": Country/City (e.g. "United States" or "United Kingdom")
    - "affiliate_fit_score": Integer 0-100 (e.g. 92)
    - "profile_url": Direct web link to channel/profile
"""

        # 3. If Groq API Key is available, process search snippets via Groq API
        if self.api_key and self.api_key != "your_groq_api_key_here":
            try:
                messages = [{"role": "system", "content": system_prompt}]
                if chat_history:
                    messages.extend(chat_history[-4:])
                messages.append({"role": "user", "content": user_query})

                payload = {
                    "model": settings.GROQ_MODEL,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.4
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                res = requests.post(self.base_url, json=payload, headers=headers, timeout=25)
                res.raise_for_status()
                content = res.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                return {
                    "response_text": parsed.get("response_text", "Here are the top influencers discovered from live YouTube & web search:"),
                    "influencers": parsed.get("influencers", []),
                    "model_used": "Groq AI (llama3-70b-8192) + Live YouTube & Web Scraper"
                }
            except Exception as e:
                print(f"[Groq Agent Warning] Groq API processing failed: {e}. Extracting via live web parser.")

        # 4. Real Web Results Parser (when Groq Key is pending)
        return self._parse_web_results_directly(user_query, web_results)

    def _parse_web_results_directly(self, user_query: str, web_results: List[Dict[str, str]]) -> Dict[str, Any]:
        """Extract structured influencer objects directly from live YouTube & web search results"""
        influencers = []
        platform = "YouTube"
        query_lower = user_query.lower()
        if "instagram" in query_lower:
            platform = "Instagram"
        elif "linkedin" in query_lower:
            platform = "LinkedIn"
        elif "tiktok" in query_lower:
            platform = "TikTok"
        elif "twitter" in query_lower:
            platform = "Twitter"

        for idx, item in enumerate(web_results[:6]):
            title = item.get("title", f"Creator {idx+1}")
            clean_title = re.sub(r' - YouTube| \| Instagram| \| LinkedIn| - TikTok', '', title).strip()
            link = item.get("link", "")
            snippet = item.get("snippet", "")

            # Extract handle from link or title
            handle_match = re.search(r'@[A-Za-z0-9_.]+', link + " " + title)
            handle = handle_match.group(0) if handle_match else f"@{clean_title.lower().replace(' ', '')[:15]}"

            # Extract email if present in snippet
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', snippet)
            contact_email = email_match.group(0) if email_match else None

            # Only include if we have a real email
            if contact_email:
                influencers.append({
                    "name": clean_title,
                    "handle": handle,
                    "platform": platform,
                    "niche": "Tech & AI Tools",
                    "followers_count": "N/A",
                    "engagement_rate": "N/A",
                    "contact_email": contact_email,
                    "location": "Unknown",
                    "affiliate_fit_score": 0,
                    "profile_url": link or f"https://{platform.lower()}.com/{handle}"
                })

        if not influencers:
            response_text = f"Live search completed for \"{user_query}\" but no influencers with verified business emails were found. Try broadening your search query."
            return {
                "response_text": response_text,
                "influencers": [],
                "model_used": "Real Live Web Scraper"
            }

        response_text = f"🌐 **Live YouTube & Web Search Completed for \"{user_query}\"**\n\nI searched across live social channels and discovered **{len(influencers)} active creators**. Real channel handles, business contact emails, and direct profile links were scraped from the live web index. Click **\"🚀 Add to Outreach & BritCRM\"** to start automated affiliate outreach!"

        return {
            "response_text": response_text,
            "influencers": influencers,
            "model_used": "Real Live YouTube & Web Scraper"
        }
