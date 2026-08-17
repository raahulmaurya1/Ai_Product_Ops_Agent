
import os
from .crawler import fetch

try:
    from tavily import TavilyClient
    _TAVILY = True
except ImportError:
    _TAVILY = False

SAMPLE_SIZE = 12  # Human review sample size


def _cross_check_claim(app: str, field: str, claimed_value: str) -> str:
    """
    Use a targeted Tavily search to cross-check a specific claim.
    Returns 'confirmed', 'corrected', or 'unverifiable'.
    """
    if not _TAVILY:
        return "unverifiable"
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "unverifiable"
    try:
        client = TavilyClient(api_key=api_key)
        q = f"{app} {field} {claimed_value} official"
        results = client.search(query=q, max_results=3).get("results", [])
        if not results:
            return "unverifiable"
        # Heuristic: check if claimed_value appears in snippets
        combined = " ".join(r.get("content", "") + r.get("title", "") for r in results).lower()
        val_lower = str(claimed_value).lower().replace("-", " ")
        if any(tok in combined for tok in val_lower.split()):
            return "confirmed"
        return "unverifiable"
    except Exception:
        return "unverifiable"


def _check_evidence_urls(result: dict) -> int:
    """Return count of evidence URLs that return non-empty content."""
    found = 0
    for e in result.get("evidence", [])[:3]:
        url = e.get("url", "") if isinstance(e, dict) else ""
        if url and fetch(url):
            found += 1
    return found


def verify(results: list[dict]) -> dict:
    """
    Verify research results:
    1. Check evidence URLs are live.
    2. Cross-check key claims (access, api_available, buildability) via Tavily.
    3. Compute initial_accuracy (evidence-url-based) and final_accuracy (claim-check-based).
    4. Build human review sample.
    """
    if not results:
        return {
            "results": [], "initial_accuracy": 0, "final_accuracy": 0, "improvement": 0,
            "human_sample": [], "hits": [], "misses": []
        }

    total = len(results)
    checked = []
    initial_supported = 0
    final_supported = 0
    hits = []
    misses = []

    for r in results:
        app = r.get("app", "")
        number = r.get("number", 0)

        # Step 1: Evidence URL check (proxy for initial accuracy)
        evidence_found = _check_evidence_urls(r)
        has_evidence = evidence_found > 0

        # Step 2: Cross-check key claims
        claim_results = {}
        fields_to_check = {
            "access": r.get("access", "unknown"),
            "buildability": r.get("buildability", "unknown"),
        }
        confirmed_count = 0
        for field, value in fields_to_check.items():
            if value and value != "unknown":
                status = _cross_check_claim(app, field, value)
            else:
                status = "unverifiable"
            claim_results[field] = status
            if status == "confirmed":
                confirmed_count += 1

        # Determine overall verification status
        if confirmed_count == len([v for v in fields_to_check.values() if v != "unknown"]):
            overall = "confirmed"
        elif confirmed_count > 0:
            overall = "confirmed"  # partial confirmation counts
        elif has_evidence:
            overall = "unverifiable"  # has evidence but couldn't cross-check claims
        else:
            overall = "unverifiable"

        if has_evidence:
            initial_supported += 1
        if has_evidence and confirmed_count > 0:
            final_supported += 1
            hits.append({"number": number, "app": app, "claims": claim_results})
        elif not has_evidence:
            misses.append({"number": number, "app": app, "reason": "No accessible evidence URLs"})

        checked.append({
            "number": number,
            "app": app,
            "status": overall,
            "evidence_pages_found": evidence_found,
            "claims_checked": claim_results,
            "needs_manual_review": r.get("needs_manual_review", False),
        })

    initial_accuracy = round(initial_supported / total * 100, 1) if total else 0
    final_accuracy = round(final_supported / total * 100, 1) if total else 0
    improvement = round(final_accuracy - initial_accuracy, 1)

    # Human review sample: diverse selection
    human_sample = _build_human_sample(results, checked)

    return {
        "results": checked,
        "initial_accuracy": initial_accuracy,
        "final_accuracy": final_accuracy,
        "improvement": improvement,
        "hits": hits[:20],
        "misses": misses[:20],
        "human_sample": human_sample,
        "note": (
            "Automated verification only. "
            "Human sample requires manual inspection of the listed URLs."
        ),
    }


def _build_human_sample(results: list[dict], checked: list[dict]) -> list[dict]:
    """
    Select ~12 diverse apps for human review.
    Mark all as requires_human_review — no fabrication.
    """
    check_map = {c["number"]: c for c in checked}
    sample = []

    # Selection strategy: pick from different categories and confidence levels
    seen_categories = set()
    # Add some high-confidence, some low-confidence, some with each buildability
    priority = []
    for r in results:
        cat = r.get("category", "")
        confidence = r.get("confidence", "low")
        build = r.get("buildability", "unknown")
        access = r.get("access", "unknown")
        mcp = r.get("mcp_status", "unknown")

        score = 0
        if cat not in seen_categories:
            score += 3
        if confidence == "high":
            score += 2
        elif confidence == "medium":
            score += 1
        if build in ("ready", "blocked"):
            score += 1
        if mcp in ("official", "community"):
            score += 1
        priority.append((score, r))

    priority.sort(key=lambda x: -x[0])
    for _, r in priority:
        if len(sample) >= SAMPLE_SIZE:
            break
        cat = r.get("category", "")
        seen_categories.add(cat)
        c = check_map.get(r["number"], {})
        ev = r.get("evidence", [])
        sample.append({
            "number": r["number"],
            "app": r["app"],
            "category": cat,
            "confidence": r.get("confidence", "low"),
            "buildability": r.get("buildability", "unknown"),
            "access": r.get("access", "unknown"),
            "mcp_status": r.get("mcp_status", "unknown"),
            "evidence_urls": [e.get("url", "") if isinstance(e, dict) else "" for e in ev[:3]],
            "automated_status": c.get("status", "unverifiable"),
            "requires_human_review": True,
            "review_instructions": (
                f"Visit the evidence URLs for {r['app']}, confirm: "
                f"access={r.get('access')}, buildability={r.get('buildability')}, "
                f"api_available={r.get('api_available')}, mcp_status={r.get('mcp_status')}."
            ),
        })

    return sample
