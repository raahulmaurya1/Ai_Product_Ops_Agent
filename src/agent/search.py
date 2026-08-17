
import os
from tavily import TavilyClient


def search_app(app: str, hint: str, hint_url: str = "", max_results: int = 4) -> list[dict]:
    """Run targeted Tavily searches for an app and return deduplicated results."""
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    # Build queries: use hint URL as domain filter when available
    queries = [
        f"{app} API documentation developer",
        f"{app} API authentication OAuth API key developer access",
        f"{app} developer pricing free trial API access",
        f"{app} MCP Model Context Protocol server",
    ]

    # Extract domain from hint_url for domain-biased search
    domain = None
    if hint_url and hint_url.startswith("http"):
        try:
            from urllib.parse import urlparse
            domain = urlparse(hint_url).netloc.lstrip("www.")
        except Exception:
            pass

    results = []
    for i, q in enumerate(queries):
        try:
            kwargs = {"query": q, "max_results": max_results}
            # Include domain hint for first query to prioritise official source
            if domain and i == 0:
                kwargs["include_domains"] = [domain]
            resp = client.search(**kwargs)
            results.extend(resp.get("results", []))
        except Exception as e:
            print(f"  [search] query failed: {q!r} → {e}")

    # Deduplicate by URL
    seen, unique = set(), []
    for r in results:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(r)

    return unique
