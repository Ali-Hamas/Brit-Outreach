"""Lead scoring 0-100 (v1 core).

Higher score = better prospect. A lead is valuable when their site has
fixable problems (that's the pitch) AND they're an established business
(reviews/rating) worth selling to.
"""
from app.services.lead_discovery.audit import SEVERITY_WEIGHT


def score_lead(lead):
    """Return an int 0-100. Combines audit-issue severity with business signals."""
    score = 0

    # Problems are opportunity: sum severity weights, cap contribution at 70.
    issues = lead.get("audit_issues") or []
    problem_points = sum(SEVERITY_WEIGHT.get(i.get("severity"), 0) for i in issues)
    score += min(problem_points, 70)

    # Established business signal (has real reviews) — worth the outreach effort.
    reviews = lead.get("user_ratings_total") or 0
    if reviews >= 100:
        score += 20
    elif reviews >= 25:
        score += 15
    elif reviews >= 5:
        score += 8

    # A contactable business (website exists) is actionable.
    if lead.get("website"):
        score += 10

    return max(0, min(100, score))
