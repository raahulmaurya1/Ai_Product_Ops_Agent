
import argparse, json, os, re, sys
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError with emojis)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

from .search import search_app
from .crawler import fetch
from .extractor import extract
from .verify import verify
from .analyze import analyze
from .report import report

RESULTS_FILE = Path("data/results.json")
VERIFICATION_FILE = Path("data/verification.json")
REPORT_FILE = Path("reports/index.html")

CATEGORY_MAP = {
    range(1, 11):   "CRM and Sales",
    range(11, 21):  "Support and Helpdesk",
    range(21, 31):  "Communications and Messaging",
    range(31, 41):  "Marketing, Ads, Email and Social",
    range(41, 51):  "Ecommerce",
    range(51, 61):  "Data, SEO and Scraping",
    range(61, 71):  "Developer, Infra and Data platforms",
    range(71, 81):  "Productivity and Project Management",
    range(81, 91):  "Finance and Fintech",
    range(91, 101): "AI, Research and Media-native",
}


def get_category(n: int) -> str:
    for rng, name in CATEGORY_MAP.items():
        if n in rng:
            return name
    return "Unknown"


def parse_readme(path="README.md") -> list[dict]:
    """Parse 100 apps from the README markdown table."""
    text = Path(path).read_text(encoding="utf-8")

    # Match table rows: | number | App Name | hint |
    rows = re.findall(
        r'^\|\s*(\d{1,3})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
        text, re.MULTILINE
    )

    apps = []
    for raw_n, raw_name, raw_hint in rows:
        n = int(raw_n)
        if not (1 <= n <= 100):
            continue
        # Skip header rows
        name_clean = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', raw_name).strip()
        if name_clean.lower() in {"app", "#", ""}:
            continue
        hint_clean = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', raw_hint).strip()
        # Extract the first URL from hint if present
        url_match = re.search(r'\(([^)]+)\)', raw_hint)
        hint_url = url_match.group(1) if url_match else hint_clean

        apps.append({
            "number": n,
            "name": name_clean,
            "hint": hint_clean,
            "hint_url": hint_url,
            "category": get_category(n),
        })

    # Deduplicate by number, keep first occurrence
    seen = {}
    for a in apps:
        if a["number"] not in seen:
            seen[a["number"]] = a
    apps = [seen[n] for n in sorted(seen)]

    return apps


def validate_apps(apps: list[dict]) -> None:
    """Validate exactly 100 apps, numbers 1–100, no gaps."""
    found = {a["number"] for a in apps}
    missing = set(range(1, 101)) - found
    extra = found - set(range(1, 101))
    errors = []
    if len(apps) != 100:
        errors.append(f"Expected 100 apps, found {len(apps)}")
    if missing:
        errors.append(f"Missing app numbers: {sorted(missing)}")
    if extra:
        errors.append(f"Extra app numbers outside 1–100: {sorted(extra)}")
    if errors:
        raise RuntimeError("README validation failed:\n" + "\n".join(errors))
    print(f"[OK] README validated: exactly 100 apps found (#{apps[0]['number']}-#{apps[-1]['number']})")


def load_existing_results() -> dict[int, dict]:
    """Load previously saved results, keyed by app number."""
    if RESULTS_FILE.exists():
        try:
            data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return {r["number"]: r for r in data if isinstance(r, dict) and "number" in r}
        except Exception:
            pass
    return {}


def save_results(results: list[dict]) -> None:
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")


def run_research(apps: list[dict], limit: int) -> list[dict]:
    """Run the research pipeline, resuming from saved results."""
    existing = load_existing_results()
    results_map = dict(existing)

    to_process = [a for a in apps[:limit] if a["number"] not in results_map]
    already_done = len(apps[:limit]) - len(to_process)

    if already_done:
        print(f"[INFO] Resuming: {already_done} apps already completed, {len(to_process)} remaining.")

    # All results ordered by number (existing + new)
    all_results = list(results_map.values())

    for app in to_process:
        print(f"\n[{app['number']:03d}/100] {app['name']} ({app['category']})")

        # Search
        sources = search_app(app["name"], app["hint"], app.get("hint_url", ""))
        print(f"  Found {len(sources)} search results")

        # Crawl: gather up to top 3 usable sources
        evidence_urls = []
        combined_text_parts = []
        for s in sources[:8]:
            if len(combined_text_parts) >= 3:
                break
            url = s.get("url", "")
            if not url:
                continue
            text = fetch(url)
            if text:
                combined_text_parts.append(f"--- SOURCE: {url} ---\n{text}")
                evidence_urls.append({"url": url, "title": s.get("title", "")})

        if not combined_text_parts:
            print(f"  [WARN] No accessible sources - marking for manual review")
            result = {
                "number": app["number"], "app": app["name"], "category": app["category"],
                "description": "", "auth": [], "access": "unknown", "api_available": False,
                "api_type": [], "api_breadth": "unknown", "mcp_status": "unknown",
                "mcp_url": None, "buildability": "unknown", "blocker": "No accessible source",
                "evidence": [], "confidence": "low", "needs_manual_review": True,
            }
            all_results.append(result)
            save_results(sorted(all_results, key=lambda r: r["number"]))
            continue

        source_text = "\n\n".join(combined_text_parts)
        print(f"  Crawled {len(combined_text_parts)} source(s), {len(source_text):,} chars")

        # Extract via Gemma
        result_obj = extract(
            number=app["number"],
            app=app["name"],
            category=app["category"],
            evidence_urls=[e["url"] for e in evidence_urls],
            text=source_text,
        )

        result = result_obj.model_dump()
        # Merge in crawled evidence if Gemma returned none
        if not result.get("evidence"):
            result["evidence"] = evidence_urls[:3]

        status = "[OK]" if not result.get("needs_manual_review") else "[WARN]"
        print(f"  {status} buildability={result.get('buildability')} access={result.get('access')} confidence={result.get('confidence')}")

        all_results.append(result)
        save_results(sorted(all_results, key=lambda r: r["number"]))

    # Return in original order
    return sorted(all_results, key=lambda r: r["number"])


def main():
    parser = argparse.ArgumentParser(description="AI Product Ops Research Agent")
    parser.add_argument("--limit", type=int, default=3, help="Number of apps to process (default 3)")
    parser.add_argument("--all", action="store_true", help="Process all 100 apps")
    parser.add_argument("--verify", action="store_true", help="Run verification pass on saved results")
    parser.add_argument("--report", action="store_true", help="Generate HTML report from saved results")
    args = parser.parse_args()

    # Always parse and validate README first
    apps = parse_readme()
    validate_apps(apps)

    if args.verify:
        print("\n=== VERIFICATION PASS ===")
        results = load_existing_results()
        if not results:
            print("No results found. Run research first.")
            sys.exit(1)
        results_list = sorted(results.values(), key=lambda r: r["number"])
        verification = verify(results_list)
        VERIFICATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        VERIFICATION_FILE.write_text(json.dumps(verification, indent=2), encoding="utf-8")
        print(f"Verification done. Initial: {verification['initial_accuracy']}% → Final: {verification['final_accuracy']}%")
        return

    if args.report:
        print("\n=== REPORT GENERATION ===")
        results = load_existing_results()
        if not results:
            print("No results found. Run research first.")
            sys.exit(1)
        results_list = sorted(results.values(), key=lambda r: r["number"])
        verification = json.loads(VERIFICATION_FILE.read_text()) if VERIFICATION_FILE.exists() else {"initial_accuracy": 0, "final_accuracy": 0, "improvement": 0, "results": []}
        analysis = analyze(results_list, verification)
        ts_path = report(results_list, analysis)
        print(f"[OK] Report generated:")
        print(f"     Timestamped : {ts_path}")
        print(f"     Latest      : {REPORT_FILE}")
        return

    # Normal research run
    limit = 100 if args.all else args.limit
    print(f"\n=== RESEARCH: processing {limit} app(s) ===")
    results = run_research(apps, limit)

    print(f"\n=== VERIFICATION ===")
    verification = verify(results)
    VERIFICATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERIFICATION_FILE.write_text(json.dumps(verification, indent=2), encoding="utf-8")

    print(f"\n=== ANALYSIS + REPORT ===")
    analysis = analyze(results, verification)
    ts_path = report(results, analysis)
    print(f"[OK] Report generated:")
    print(f"     Timestamped : {ts_path}")
    print(f"     Latest      : {REPORT_FILE}")

    total = len(results)
    manual = sum(1 for r in results if r.get("needs_manual_review"))
    print(f"\n[DONE]")
    print(f"   Apps processed : {total}")
    print(f"   Manual review  : {manual}")
    print(f"   Initial accuracy: {verification['initial_accuracy']}%")
    print(f"   Final accuracy  : {verification['final_accuracy']}%")
    print(f"   Report         : {REPORT_FILE}")


if __name__ == "__main__":
    main()
