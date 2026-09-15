"""Social Listening API endpoints for Reddit, Google CSE, and AI reply drafting."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.lead_discovery.reddit_service import search_reddit, DEFAULT_SUBREDDITS, DEFAULT_KEYWORDS
from app.services.lead_discovery.google_cse_service import search_google_cse
from app.services.lead_discovery.groq_service import generate_draft_reply

router = APIRouter(prefix="/social-listening", tags=["Social Listening"])


class RedditSearchRequest(BaseModel):
    keywords: Optional[str] = None
    subreddits: Optional[str] = None
    limit: int = 25


class GoogleCSESearchRequest(BaseModel):
    query: str
    site_filter: Optional[str] = None
    limit: int = 10


class DraftReplyRequest(BaseModel):
    title: str
    content: str
    author: Optional[str] = ""
    platform: Optional[str] = ""
    subreddit: Optional[str] = ""


class RedditResult(BaseModel):
    post_id: Optional[str]
    title: str
    subreddit: str
    author: str
    post_url: str
    upvotes: int
    created_at: str
    content: str
    num_comments: int
    source: str


class GoogleCSEResult(BaseModel):
    title: str
    snippet: str
    link: str
    domain: str
    platform: str
    content: str
    source: str


@router.get("/reddit/defaults")
async def get_reddit_defaults():
    """Get default subreddits and keywords for Reddit search."""
    return {
        "default_subreddits": DEFAULT_SUBREDDITS,
        "default_keywords": DEFAULT_KEYWORDS,
    }


@router.post("/reddit/search")
async def search_reddit_endpoint(request: RedditSearchRequest):
    """Search Reddit for posts matching keywords in specified subreddits."""
    results, error = search_reddit(
        keywords=request.keywords,
        subreddits=request.subreddits,
        limit=request.limit,
    )
    if error and not results:
        raise HTTPException(status_code=400, detail=error)
    return {
        "results": results,
        "count": len(results),
        "warning": error if error else None,
    }


@router.post("/google/search")
async def search_google_cse_endpoint(request: GoogleCSESearchRequest):
    """Search Google Custom Search for posts across platforms."""
    results, error = search_google_cse(
        query=request.query,
        site_filter=request.site_filter,
        limit=request.limit,
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "results": results,
        "count": len(results),
    }


@router.post("/draft-reply")
async def draft_reply_endpoint(request: DraftReplyRequest):
    """Generate an AI-drafted reply for a social post using Groq."""
    reply, error = generate_draft_reply(
        post_title=request.title,
        post_content=request.content,
        author=request.author,
        platform=request.platform,
        subreddit=request.subreddit,
    )
    if error:
        raise HTTPException(status_code=500, detail=error)
    return {"reply": reply}
