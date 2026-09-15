"""Google Custom Search JSON API service.

Uses official Google Custom Search API (100 free queries/day).
Searches platforms (Reddit, Twitter/X, forums, etc.) using site: operators.
"""
import os
import requests


def search_google_cse(query, site_filter=None, limit=10):
    """Search Google Custom Search JSON API.

    :param query: search query string, e.g. "looking for AI automation agency"
    :param site_filter: optional platform filter e.g. "reddit.com", "x.com", "twitter.com"
    :param limit: number of results (1 to 10)
    :return: (results_list, error_string)
    """
    api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        return [], "Google Custom Search is unavailable: GOOGLE_CUSTOM_SEARCH_API_KEY / GOOGLE_CSE_ID not set."

    final_query = query.strip()
    if site_filter:
        clean_site = site_filter.strip()
        if clean_site.lower().startswith("site:"):
            clean_site = clean_site[5:].strip()
        clean_site = clean_site.replace("http://", "").replace("https://", "").split("/")[0]
        if clean_site and not final_query.lower().startswith("site:") and "site:" not in final_query.lower():
            final_query = f"{final_query} site:{clean_site}"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": final_query,
        "num": min(max(1, limit), 10),
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200:
            err_data = {}
            try:
                err_data = res.json().get("error", {})
            except Exception:
                pass
            msg = err_data.get("message") or f"Google CSE API returned HTTP {res.status_code}."
            return [], msg

        try:
            data = res.json()
        except Exception as exc:
            return [], f"Failed to parse Google CSE response: {str(exc)}"

        items = data.get("items", [])
        results = []
        for item in items:
            link = item.get("link", "")
            domain = item.get("displayLink", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")

            # Identify platform and source from domain/link
            platform = "Google Search"
            source = "Google Search"
            if "linkedin.com" in link:
                source = "LinkedIn"
                if "/in/" in link:
                    platform = "LinkedIn Profile"
                elif "/posts/" in link or "/pulse/" in link or "/feed/" in link:
                    platform = "LinkedIn Post"
                elif "/company/" in link:
                    platform = "LinkedIn Company"
                else:
                    platform = "LinkedIn (Google)"
            elif "reddit.com" in link:
                source = "Reddit"
                platform = "Reddit (Google)"
            elif "twitter.com" in link or "x.com" in link:
                source = "Twitter/X"
                platform = "Twitter/X (Google)"
            elif "facebook.com" in link:
                source = "Facebook"
                platform = "Facebook (Google)"
            elif "instagram.com" in link:
                source = "Instagram"
                platform = "Instagram (Google)"

            results.append({
                "title": title,
                "snippet": snippet,
                "link": link,
                "domain": domain,
                "platform": platform,
                "content": f"{title}\n{snippet}",
                "source": source,
            })
        return results, None

    except Exception as exc:
        return [], f"Google Custom Search failed: {str(exc)}"
