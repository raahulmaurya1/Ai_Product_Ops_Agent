
import json, os, re
import httpx
from .models import ResearchResult

SYSTEM = """You are a research assistant extracting API and integration facts about software products.
Return JSON only. No markdown. No explanation. No code fences.
Do not invent facts. Use "unknown" for any field where evidence is insufficient.
Fields with list types should be arrays. All enum fields must match exactly."""

SCHEMA = {
    "number": 0,
    "app": "string",
    "category": "string",
    "description": "one-sentence description of what the app does",
    "auth": ["list of: OAuth2 | API key | Basic | token | other"],
    "access": "self-serve-free | self-serve-trial | paid-gated | partner-gated | contact-sales | unknown",
    "api_available": "true or false (boolean)",
    "api_type": ["list of: REST | GraphQL | SDK | CLI | Webhook | other"],
    "api_breadth": "broad | moderate | narrow | none | unknown",
    "mcp_status": "official | community | mentioned | none | unknown",
    "mcp_url": "string or null",
    "buildability": "ready | buildable | partial | blocked | unknown",
    "blocker": "string or null",
    "evidence": [{"url": "string", "title": "string", "claim": "string", "snippet": "string"}],
    "confidence": "high | medium | low",
    "needs_manual_review": "true or false (boolean)"
}


def _call_gemma(prompt: str, timeout: int = 90) -> str:
    """Call the self-hosted Gemma via OpenAI-compatible endpoint."""
    base_url = os.environ.get("GEMMA_API_URL", "").rstrip("/")
    if not base_url or base_url == "YOUR_GEMMA_API_URL_HERE":
        raise RuntimeError("GEMMA_API_URL is not configured. Set it in .env to your ngrok URL.")

    # Strip any path suffix the user may have included so we build the URL cleanly
    for suffix in ("/v1/chat/completions", "/chat/completions", "/v1"):
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)]
            break

    api_key = os.environ.get("GEMMA_API_KEY", "")
    model = os.environ.get("GEMMA_MODEL", "gemma-4-26b")

    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
    }

    resp = httpx.post(
        f"{base_url}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def extract(number: int, app: str, category: str, evidence_urls: list, text: str) -> ResearchResult:
    """Send source text to Gemma and parse structured ResearchResult."""
    schema_str = json.dumps(SCHEMA, indent=2)
    prompt = f"""APP: {app}
CATEGORY: {category}
SOURCE URLS: {json.dumps(evidence_urls[:3])}

SOURCE TEXT (extracted from official docs/pages):
{text[:12000]}

Return ONLY valid JSON matching this schema. No markdown, no prose, no fences:
{schema_str}

Set number={number}, app="{app}", category="{category}".
Populate evidence[] with actual URLs from SOURCE URLS above plus the claims they support."""

    last_error = None
    for attempt in range(3):
        try:
            raw = _call_gemma(prompt if attempt == 0 else prompt + f"\n\nPrevious attempt produced invalid JSON. Error: {last_error}\nReturn ONLY valid JSON.")
            # Strip markdown fences if model misbehaves
            raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
            raw = re.sub(r"\s*```$", "", raw.strip())
            raw = raw.strip()
            parsed = json.loads(raw)
            # Ensure required identity fields
            parsed["number"] = number
            parsed["app"] = app
            parsed["category"] = category
            # Coerce boolean strings if model returns them as strings
            if isinstance(parsed.get("api_available"), str):
                parsed["api_available"] = parsed["api_available"].lower() == "true"
            if isinstance(parsed.get("needs_manual_review"), str):
                parsed["needs_manual_review"] = parsed["needs_manual_review"].lower() == "true"
            return ResearchResult.model_validate(parsed)
        except Exception as e:
            last_error = str(e)
            print(f"  [extractor] attempt {attempt+1} failed: {e}")

    print(f"  [extractor] all retries exhausted for {app}, marking for manual review")
    return ResearchResult(
        number=number,
        app=app,
        category=category,
        needs_manual_review=True,
        confidence="low",
        description="Extraction failed after 3 attempts.",
    )
