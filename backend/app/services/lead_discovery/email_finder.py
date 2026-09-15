"""Contact email discovery + verification.

find_contact_email(): Guesses common email patterns from a website domain.
verify_email(): Basic syntax validation. For real verification, integrate
Hunter.io, NeverBounce, or ZeroBounce via environment variables.
"""
import os
import re
from urllib.parse import urlparse
import requests


DECISION_ROLES = ("owner", "founder", "ceo", "marketing", "director", "manager")


def _domain(website):
    if not website:
        return None
    parsed = urlparse(website if "://" in website else "http://" + website)
    host = parsed.netloc or parsed.path.split("/")[0]
    return host[4:] if host.startswith("www.") else host


def find_contact_email(website):
    """Return {email, confidence, source, verified} or an {error} dict."""
    domain = _domain(website)
    if not domain:
        return {"email": None, "confidence": None, "source": None, "verified": None,
                "error": "No website domain to search."}

    # Try Hunter.io if key is available
    hunter_key = os.getenv("HUNTER_API_KEY")
    if hunter_key:
        result = _hunter_domain_search(domain, hunter_key)
        if result:
            return result

    # Fallback: guess common patterns
    return {
        "email": f"info@{domain}",
        "confidence": None,
        "source": "pattern",
        "verified": "unverified",
        "note": "Guessed from common pattern — verify before sending.",
    }


def _hunter_domain_search(domain, api_key):
    try:
        resp = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={"domain": domain, "api_key": api_key},
            timeout=10,
        )
        data = resp.json()
        emails = (data.get("data") or {}).get("emails") or []
        if not emails:
            return None

        def rank(e):
            dept = (e.get("department") or "").lower()
            position = (e.get("position") or "").lower()
            role_hit = any(r in dept or r in position for r in DECISION_ROLES)
            return (role_hit, e.get("confidence") or 0)

        best = max(emails, key=rank)
        return {
            "email": best.get("value"),
            "confidence": best.get("confidence"),
            "source": "hunter",
            "verified": None,
        }
    except Exception:
        return None


def verify_email(email):
    """Return one of valid | risky | invalid | unverified."""
    if not email:
        return {"verified": "invalid", "error": "No email to verify."}

    # Basic syntax check
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return {"verified": "invalid", "error": "Invalid email format."}

    # Check disposable domains
    disposable = ('mailinator.com', 'tempmail.com', 'throwaway.com', 'guerrillamail.com')
    domain = email.split('@')[1].lower()
    if domain in disposable:
        return {"verified": "risky", "error": "Disposable email domain."}

    return {"verified": "unverified", "error": "No verification service configured."}
