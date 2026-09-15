"""Reddit search service using Reddit's official API.

Uses Reddit OAuth client credentials if REDDIT_CLIENT_ID & REDDIT_CLIENT_SECRET
are set, or falls back to public API endpoints.
Fully compliant with Reddit API terms.
"""
import os
from datetime import datetime, timezone
import requests

DEFAULT_SUBREDDITS = [
    "entrepreneur", "smallbusiness", "webdev", "SaaS", "automation",
    "forhire", "freelance", "startups", "ArtificialInteligence"
]

DEFAULT_KEYWORDS = [
    "looking for AI automation agency",
    "looking for web developer",
    "need website redesign",
    "AI voice agent developer",
    "need n8n developer",
    "looking for app developer",
    "need SaaS MVP developer",
    "hiring frontend developer",
    "looking for WordPress developer"
]


def _get_oauth_token():
    """Acquire an application-only OAuth token from Reddit."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "BritOutreach/1.0")

    if not client_id or not client_secret:
        return None, "Missing Reddit API credentials."

    url = "https://www.reddit.com/api/v1/access_token"
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    headers = {"User-Agent": user_agent}
    data = {"grant_type": "client_credentials"}

    try:
        res = requests.post(url, auth=auth, data=data, headers=headers, timeout=10)
        if res.status_code == 200:
            try:
                token = res.json().get("access_token")
                return token, None
            except Exception:
                return None, "Failed to parse Reddit OAuth response."
        return None, f"Reddit OAuth error (HTTP {res.status_code}): {res.text[:120]}"
    except Exception as exc:
        return None, f"Reddit OAuth failed: {str(exc)}"


def search_reddit(keywords=None, subreddits=None, limit=25):
    """Search target subreddits for given keywords.

    :param keywords: search term string or list of terms
    :param subreddits: list of subreddits (without r/)
    :param limit: maximum results to fetch (1-100)
    :return: (results_list, error_string)
    """
    user_agent = os.getenv("REDDIT_USER_AGENT", "BritOutreach/1.0")

    if subreddits is None:
        subreddits = DEFAULT_SUBREDDITS
    elif isinstance(subreddits, str):
        subreddits = [s.strip().replace("r/", "") for s in subreddits.split(",") if s.strip()]

    if not keywords:
        query = " OR ".join([f'"{k}"' for k in DEFAULT_KEYWORDS[:3]])
    elif isinstance(keywords, list):
        query = " OR ".join([f'"{k}"' if " " in k else k for k in keywords])
    else:
        query = str(keywords).strip()

    subreddit_path = "+".join([s.strip().replace("r/", "") for s in subreddits if s.strip()])
    if not subreddit_path:
        subreddit_path = "+".join(DEFAULT_SUBREDDITS)

    token, auth_error = _get_oauth_token()

    headers = {"User-Agent": user_agent}
    if token:
        url = f"https://oauth.reddit.com/r/{subreddit_path}/search"
        headers["Authorization"] = f"bearer {token}"
    else:
        url = f"https://www.reddit.com/r/{subreddit_path}/search.json"

    params = {
        "q": query,
        "restrict_sr": "on",
        "sort": "new",
        "limit": min(limit, 100),
        "syntax": "plain",
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=12)
        if res.status_code != 200:
            err_msg = f"Reddit API returned HTTP {res.status_code}."
            if auth_error:
                err_msg += f" Note: {auth_error}"
            return [], err_msg

        try:
            data = res.json()
        except Exception as exc:
            return [], f"Failed to parse Reddit search response: {str(exc)}"

        children = data.get("data", {}).get("children", [])
        results = []
        for child in children:
            p = child.get("data", {})
            created_utc = p.get("created_utc")
            date_str = ""
            if created_utc:
                date_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")

            permalink = p.get("permalink", "")
            post_url = f"https://www.reddit.com{permalink}" if permalink else p.get("url", "")

            results.append({
                "post_id": p.get("id"),
                "title": p.get("title", ""),
                "subreddit": f"r/{p.get('subreddit', '')}",
                "author": p.get("author", "[deleted]"),
                "post_url": post_url,
                "upvotes": p.get("score", 0),
                "created_at": date_str,
                "content": p.get("selftext", "") or p.get("title", ""),
                "num_comments": p.get("num_comments", 0),
                "source": "Reddit",
            })
        return results, None

    except Exception as exc:
        return [], f"Reddit search failed: {str(exc)}"
