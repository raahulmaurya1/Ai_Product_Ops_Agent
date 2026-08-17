
from typing import Literal
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    url: str
    title: str = ""
    claim: str = ""
    snippet: str = ""

class ResearchResult(BaseModel):
    number: int
    app: str
    category: str
    description: str = ""
    auth: list[str] = Field(default_factory=list)
    access: Literal["self-serve-free","self-serve-trial","paid-gated","partner-gated","contact-sales","unknown"] = "unknown"
    api_available: bool = False
    api_type: list[str] = Field(default_factory=list)
    api_breadth: Literal["broad","moderate","narrow","none","unknown"] = "unknown"
    mcp_status: Literal["official","community","mentioned","none","unknown"] = "unknown"
    mcp_url: str | None = None
    buildability: Literal["ready","buildable","partial","blocked","unknown"] = "unknown"
    blocker: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: Literal["high","medium","low"] = "low"
    needs_manual_review: bool = False
