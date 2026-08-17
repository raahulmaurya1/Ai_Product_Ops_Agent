
import httpx
import trafilatura

try:
    from bs4 import BeautifulSoup
    _BS4 = True
except ImportError:
    _BS4 = False

MAX_CHARS = 12000


def fetch(url: str, timeout: int = 20) -> str:
    """Fetch a URL and return clean readable text, max MAX_CHARS characters."""
    try:
        r = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "AI-Product-Ops-Research-Agent/1.0 (research; not indexing)"},
        )
        # Silently skip 4xx/5xx pages instead of raising
        if r.status_code >= 400:
            print(f"  [crawler] HTTP {r.status_code}: {url}")
            return ""
        html_content = r.text

        # Try trafilatura first
        text = trafilatura.extract(html_content, include_links=False, include_images=False) or ""

        # Fallback to BeautifulSoup if trafilatura got nothing
        if not text.strip() and _BS4:
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)

        return text[:MAX_CHARS]

    except Exception as e:
        print(f"  [crawler] fetch failed: {url} -> {type(e).__name__}: {str(e)[:80]}")
        return ""
