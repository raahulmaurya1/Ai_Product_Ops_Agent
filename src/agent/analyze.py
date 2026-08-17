
from collections import Counter


CATEGORY_ORDER = [
    "CRM and Sales",
    "Support and Helpdesk",
    "Communications and Messaging",
    "Marketing, Ads, Email and Social",
    "Ecommerce",
    "Data, SEO and Scraping",
    "Developer, Infra and Data platforms",
    "Productivity and Project Management",
    "Finance and Fintech",
    "AI, Research and Media-native",
]


def analyze(results: list[dict], verification: dict) -> dict:
    if not results:
        return {
            "count": 0, "auth": {}, "access": {}, "api_type": {}, "mcp": {},
            "buildability": {}, "blockers": {}, "api_breadth": {},
            "categories": {}, "easy_wins": [], "outreach": [],
            "verification": verification,
        }

    # Global distributions
    auth = Counter(a for r in results for a in r.get("auth", []))
    access = Counter(r.get("access") for r in results)
    api_type = Counter(t for r in results for t in r.get("api_type", []))
    mcp = Counter(r.get("mcp_status") for r in results)
    build = Counter(r.get("buildability") for r in results)
    api_breadth = Counter(r.get("api_breadth") for r in results)
    blockers = Counter(
        r.get("blocker") for r in results
        if r.get("blocker") and r.get("blocker") not in (None, "null", "")
    )
    confidence = Counter(r.get("confidence") for r in results)

    # Category breakdown
    categories = {}
    for cat in CATEGORY_ORDER:
        cat_results = [r for r in results if r.get("category") == cat]
        if not cat_results:
            continue
        categories[cat] = {
            "count": len(cat_results),
            "buildability": dict(Counter(r.get("buildability") for r in cat_results)),
            "access": dict(Counter(r.get("access") for r in cat_results)),
            "mcp": dict(Counter(r.get("mcp_status") for r in cat_results)),
            "api_available": sum(1 for r in cat_results if r.get("api_available")),
            "ready_buildable": sum(1 for r in cat_results if r.get("buildability") in ("ready", "buildable")),
        }

    # Easy wins: public API + self-serve + broad/moderate breadth
    easy_wins = [
        {
            "number": r["number"], "app": r["app"], "category": r.get("category", ""),
            "access": r.get("access"), "api_breadth": r.get("api_breadth"),
            "mcp_status": r.get("mcp_status"), "buildability": r.get("buildability"),
            "auth": r.get("auth", []),
        }
        for r in results
        if r.get("api_available")
        and r.get("access") in ("self-serve-free", "self-serve-trial")
        and r.get("api_breadth") in ("broad", "moderate")
        and r.get("buildability") in ("ready", "buildable")
    ]

    # Outreach / gated candidates
    outreach = [
        {
            "number": r["number"], "app": r["app"], "category": r.get("category", ""),
            "access": r.get("access"), "blocker": r.get("blocker"),
            "buildability": r.get("buildability"),
        }
        for r in results
        if r.get("access") in ("paid-gated", "partner-gated", "contact-sales")
        or r.get("buildability") == "blocked"
    ]

    return {
        "count": len(results),
        "auth": dict(auth),
        "access": dict(access),
        "api_type": dict(api_type),
        "mcp": dict(mcp),
        "buildability": dict(build),
        "api_breadth": dict(api_breadth),
        "blockers": dict(blockers),
        "confidence": dict(confidence),
        "categories": categories,
        "easy_wins": easy_wins,
        "outreach": outreach,
        "verification": verification,
        "api_available_count": sum(1 for r in results if r.get("api_available")),
        "manual_review_count": sum(1 for r in results if r.get("needs_manual_review")),
    }
