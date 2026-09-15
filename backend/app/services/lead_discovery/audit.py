"""Website audit: v1 basic checks + v2.1 deep checks.

audit_website() returns a dict of audit fields plus a normalized `audit_issues`
list (each {code, label, severity, detail}). Every external call is isolated so
a single failing check never aborts the whole audit.
"""
import os
import re
import socket
import ssl
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.services.lead_discovery.http_util import request_with_backoff

PAGESPEED_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
BUILTWITH_URL = "https://api.builtwith.com/v21/api.json"

# Severity weights feed both scoring and opening-line ranking.
SEVERITY_WEIGHT = {"critical": 30, "high": 20, "medium": 12, "low": 6}


def _domain(website):
    if not website:
        return None
    parsed = urlparse(website if "://" in website else "http://" + website)
    return parsed.netloc or parsed.path.split("/")[0]


def audit_website(website):
    """Run all audit checks on a website URL. Returns a dict of fields + issues."""
    result = {
        "has_ssl": None,
        "is_mobile_friendly": None,
        "load_time_seconds": None,
        "seo_title": None,
        "seo_meta_description": None,
        "ps_mobile_score": None,
        "ps_desktop_score": None,
        "cwv_lcp": None,
        "cwv_cls": None,
        "cwv_inp": None,
        "ssl_valid": None,
        "ssl_expiry": None,
        "tech_stack": None,
        "audit_issues": [],
    }
    if not website:
        result["audit_issues"].append(
            {"code": "no_website", "label": "No website found", "severity": "critical",
             "detail": "The business has no website listed."}
        )
        return result

    _basic_fetch(website, result)
    _ssl_check(website, result)
    _pagespeed(website, result)
    _tech_stack(website, result)
    _derive_issues(result)
    return result


def _basic_fetch(website, result):
    """v1: fetch the page, measure load time, sniff SSL, title, meta description, viewport."""
    url = website if "://" in website else "https://" + website
    try:
        start = time.monotonic()
        resp = request_with_backoff("GET", url, min_interval=0.0, max_retries=1, timeout=15,
                                    headers={"User-Agent": "Mozilla/5.0 (BritOutreach audit)"})
        result["load_time_seconds"] = round(time.monotonic() - start, 2)
        result["has_ssl"] = 1 if resp.url.startswith("https://") else 0
        html = resp.text or ""
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        result["seo_title"] = title.group(1).strip()[:255] if title else None
        result["seo_meta_description"] = 1 if re.search(
            r'<meta[^>]+name=["\']description["\']', html, re.IGNORECASE) else 0
        result["is_mobile_friendly"] = 1 if re.search(
            r'<meta[^>]+name=["\']viewport["\']', html, re.IGNORECASE) else 0
    except Exception:
        result["has_ssl"] = 0 if url.startswith("http://") else result["has_ssl"]


def _ssl_check(website, result):
    """v2.1: real certificate validity + expiry via a TLS handshake (no rate-limited API)."""
    host = _domain(website)
    if not host:
        return
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        if not_after:
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            result["ssl_expiry"] = expiry.strftime("%Y-%m-%d")
            result["ssl_valid"] = 1 if expiry > datetime.now(timezone.utc).replace(tzinfo=None) else 0
    except Exception:
        result["ssl_valid"] = 0


def _pagespeed(website, result):
    """v2.1: PageSpeed Insights for mobile+desktop scores and Core Web Vitals."""
    pagespeed_key = os.getenv("GOOGLE_PAGESPEED_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY")
    if not pagespeed_key:
        return
    for strategy, score_key in (("mobile", "ps_mobile_score"), ("desktop", "ps_desktop_score")):
        try:
            resp = request_with_backoff(
                "GET", PAGESPEED_URL, min_interval=1.0, timeout=60,
                params={"url": website, "strategy": strategy,
                        "key": pagespeed_key, "category": "performance"},
            )
            data = resp.json()
            lighthouse = data.get("lighthouseResult", {})
            perf = lighthouse.get("categories", {}).get("performance", {}).get("score")
            if perf is not None:
                result[score_key] = round(perf * 100)
            if strategy == "mobile":
                _extract_cwv(data, result)
        except Exception:
            continue


def _extract_cwv(data, result):
    audits = data.get("lighthouseResult", {}).get("audits", {})
    lcp = audits.get("largest-contentful-paint", {}).get("numericValue")
    cls = audits.get("cumulative-layout-shift", {}).get("numericValue")
    inp = (audits.get("interaction-to-next-paint")
           or audits.get("experimental-interaction-to-next-paint") or {}).get("numericValue")
    if lcp is not None:
        result["cwv_lcp"] = round(lcp / 1000.0, 2)
    if cls is not None:
        result["cwv_cls"] = round(cls, 3)
    if inp is not None:
        result["cwv_inp"] = round(inp)


def _tech_stack(website, result):
    """v2.1: detect platform. Prefer BuiltWith API; fall back to HTML fingerprinting."""
    builtwith_key = os.getenv("BUILTWITH_API_KEY")
    detected = None
    if builtwith_key:
        try:
            resp = request_with_backoff(
                "GET", BUILTWITH_URL,
                params={"KEY": builtwith_key, "LOOKUP": _domain(website)},
            )
            data = resp.json()
            cms = []
            for res in data.get("Results", []):
                for path in res.get("Result", {}).get("Paths", []):
                    for tech in path.get("Technologies", []):
                        if tech.get("Tag") in ("cms", "ecommerce"):
                            cms.append(tech.get("Name"))
            if cms:
                detected = ", ".join(dict.fromkeys(cms))
        except Exception:
            detected = None
    if not detected:
        detected = _fingerprint_platform(website)
    result["tech_stack"] = detected


def _fingerprint_platform(website):
    """Lightweight, key-free platform sniff from HTML markers."""
    url = website if "://" in website else "https://" + website
    try:
        resp = request_with_backoff("GET", url, min_interval=0.0, max_retries=1, timeout=15,
                                    headers={"User-Agent": "Mozilla/5.0 (BritOutreach audit)"})
        html = (resp.text or "").lower()
        markers = [
            ("WordPress", ["wp-content", "wp-includes", "/wp-json"]),
            ("Wix", ["wix.com", "_wixcssinj", "wixstatic.com"]),
            ("Squarespace", ["squarespace.com", "static.squarespace", "sqs-"]),
            ("Shopify", ["cdn.shopify.com", "shopify.com", "myshopify"]),
            ("Webflow", ["webflow.com", "wf-"]),
            ("GoDaddy Website Builder", ["websitebuilder.godaddy", "img1.wsimg.com"]),
        ]
        for name, needles in markers:
            if any(n in html for n in needles):
                return name
        return "Custom / Unknown"
    except Exception:
        return None


def _derive_issues(result):
    """Translate raw audit fields into a ranked list of issue dicts."""
    issues = result["audit_issues"]

    if result["has_ssl"] == 0 or result["ssl_valid"] == 0:
        issues.append({"code": "no_ssl", "label": "No valid SSL certificate", "severity": "critical",
                       "detail": "The site is not securely served over HTTPS."})
    if result["is_mobile_friendly"] == 0:
        issues.append({"code": "not_mobile", "label": "Not mobile-friendly", "severity": "high",
                       "detail": "No mobile viewport tag — the site likely renders poorly on phones."})
    if result["ps_mobile_score"] is not None and result["ps_mobile_score"] < 50:
        issues.append({"code": "slow_mobile", "label": "Poor mobile performance", "severity": "high",
                       "detail": f"Mobile PageSpeed score is {result['ps_mobile_score']}/100."})
    if result["load_time_seconds"] is not None and result["load_time_seconds"] > 4:
        issues.append({"code": "slow_load", "label": "Slow page load", "severity": "medium",
                       "detail": f"The page took {result['load_time_seconds']}s to load."})
    if result["cwv_lcp"] is not None and result["cwv_lcp"] > 2.5:
        issues.append({"code": "poor_lcp", "label": "Poor Largest Contentful Paint", "severity": "medium",
                       "detail": f"LCP is {result['cwv_lcp']}s (Google recommends under 2.5s)."})
    if result["seo_title"] is None:
        issues.append({"code": "no_title", "label": "Missing page title", "severity": "medium",
                       "detail": "No <title> tag — hurts search ranking."})
    if result["seo_meta_description"] == 0:
        issues.append({"code": "no_meta", "label": "Missing meta description", "severity": "low",
                       "detail": "No meta description — search snippets will be auto-generated."})

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues.sort(key=lambda i: order.get(i["severity"], 9))
