"""Email sending via Mailgun (legacy).

Uses environment variables for configuration. Falls back gracefully
when Mailgun credentials are not configured.
"""
import os
from datetime import datetime, timezone
import requests


MAILGUN_BASE_URL = "https://api.mailgun.net"


def _get_config():
    return {
        "api_key": os.getenv("MAILGUN_API_KEY"),
        "domain": os.getenv("MAILGUN_DOMAIN"),
        "from_email": os.getenv("OUTREACH_FROM_EMAIL"),
        "daily_cap": int(os.getenv("DAILY_SEND_CAP", "50")),
    }


def sends_today():
    """Count successful sends today. Stub for legacy compatibility."""
    return 0


def can_send():
    """Return (allowed, reason)."""
    cfg = _get_config()
    if not cfg["api_key"] or not cfg["domain"] or not cfg["from_email"]:
        return False, "Mailgun not configured (set MAILGUN_API_KEY, MAILGUN_DOMAIN, OUTREACH_FROM_EMAIL)"
    used = sends_today()
    if used >= cfg["daily_cap"]:
        return False, f"Daily send cap reached ({used}/{cfg['daily_cap']})"
    return True, f"{used}/{cfg['daily_cap']} sent today"


def send_email(lead_id, to_email, subject, body):
    """Send one email through Mailgun. Returns {ok, message}."""
    allowed, reason = can_send()
    if not allowed:
        return {"ok": False, "message": reason}
    if not to_email:
        return {"ok": False, "message": "No recipient email address."}

    cfg = _get_config()
    url = f"{MAILGUN_BASE_URL}/v3/{cfg['domain']}/messages"

    try:
        resp = requests.post(
            url,
            auth=("api", cfg["api_key"]),
            data={"from": cfg["from_email"], "to": to_email,
                  "subject": subject, "text": body},
            timeout=15,
        )
        ok = resp.status_code == 200
        return {"ok": ok, "message": "Sent." if ok else f"Failed: {resp.text[:200]}"}
    except Exception as exc:
        return {"ok": False, "message": f"Send error: {str(exc)[:200]}"}
