from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class UnderwritingType(str, Enum):
    PROPERTY = "property"


class UnderwritingRequest(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=500)
    address: str = Field(..., min_length=1, max_length=2000)
    type: UnderwritingType
    underwriting_questions: list[str] = Field(..., min_length=1)


class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    content: str | None = None
    source: str | None = None
    extraction_status: str = "pending"
    extraction_error: str | None = None


class Evidence(BaseModel):
    evidence_id: str
    title: str
    url: HttpUrl
    source: str
    content: str
    relevance: str
    published_date: str | None = None


class UnderwritingInsight(BaseModel):
    question: str
    finding: str
    risk_implication: str
    confidence: str
    evidence_ids: list[str] = Field(default_factory=list)


class UnderwritingReport(BaseModel):
    account_name: str
    address: str
    type: UnderwritingType
    executive_summary: str
    insights: list[UnderwritingInsight]
    evidence: list[Evidence]
    information_gaps: list[str] = Field(default_factory=list)
    recommended_follow_up_questions: list[str] = Field(default_factory=list)
    research_timestamp: datetime