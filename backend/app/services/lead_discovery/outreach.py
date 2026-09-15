"""Opening-line generation + full email draft.

Template-based, no LLM. Picks the most compelling audit issue and builds
one specific sentence referencing the business's real problem.
"""
import os


# One template per issue code. {biz} and issue-specific values get filled in.
_OPENING_TEMPLATES = {
    "no_website": "Noticed {biz} doesn't have a website yet — you're likely losing "
                  "customers who search for you online and find a competitor instead.",
    "no_ssl": "Noticed {biz}'s site isn't secured with SSL, so browsers now flag it as "
              "\"Not Secure\" — that warning scares off visitors before they ever see your offer.",
    "not_mobile": "Noticed {biz}'s site isn't mobile-friendly, and since most local searches "
                  "happen on a phone, a lot of potential customers are bouncing straight away.",
    "slow_mobile": "Noticed {biz}'s site scores {ps_mobile}/100 for mobile speed — slow pages "
                   "push visitors to hit back before the page even finishes loading.",
    "slow_load": "Noticed {biz}'s site takes about {load}s to load, and every extra second at "
                 "that range measurably drops the number of visitors who stick around.",
    "poor_lcp": "Noticed {biz}'s main content takes {lcp}s to appear on mobile (Google wants "
                "under 2.5s) — it's the kind of thing that quietly costs you search ranking.",
    "no_title": "Noticed {biz}'s homepage is missing a proper page title, which makes it much "
                "harder for people to find you on Google.",
    "no_meta": "Noticed {biz}'s site is missing a meta description, so its Google listing shows "
               "a random snippet instead of a compelling reason to click.",
}

_GENERIC_OPENING = ("Took a quick look at {biz}'s website and spotted a few things that are "
                    "probably costing you customers online.")


def generate_opening_line(lead):
    """Return one personalized opening sentence based on the top-ranked issue."""
    biz = lead.get("business_name") or "your business"
    issues = lead.get("audit_issues") or []
    if not issues:
        return _GENERIC_OPENING.format(biz=biz)

    top = issues[0]
    template = _OPENING_TEMPLATES.get(top["code"], _GENERIC_OPENING)
    return template.format(
        biz=biz,
        ps_mobile=lead.get("ps_mobile_score"),
        load=lead.get("load_time_seconds"),
        lcp=lead.get("cwv_lcp"),
    )


def build_email_draft(lead, opening_line=None):
    """Assemble a full outreach email (subject + body) around the opening line."""
    biz = lead.get("business_name") or "there"
    opening = opening_line or lead.get("opening_line") or generate_opening_line(lead)
    company = os.getenv("COMPANY_NAME", "Britsync AI")
    sender = os.getenv("COMPANY_SENDER_NAME", "the Britsync AI team")

    cta = "Would you be open to a quick 15-minute call this week to walk through it?"
    calendar_link = os.getenv("COMPANY_CALENDAR_LINK")
    if calendar_link:
        cta += f"\nYou can grab a time here: {calendar_link}"

    subject = f"Quick note about {biz}'s website"
    body = (
        f"Hi {biz} team,\n\n"
        f"{opening}\n\n"
        f"We're {company} — we help local businesses fix exactly these kinds of issues "
        f"(site speed, mobile experience, security, and search visibility) so their website "
        f"actually brings in customers instead of turning them away.\n\n"
        f"{cta}\n\n"
        f"Best,\n{sender}"
    )
    return {"subject": subject, "body": body}
