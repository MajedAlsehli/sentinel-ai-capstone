from typing import Any, Literal

from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    destination: Literal["email_agent", "url_agent", "ip_agent", "file_agent"]
    reason: str = Field(min_length=8)


class SpecialistAssessment(BaseModel):
    """Structured conclusion produced after the specialist sees tool results."""

    summary: str
    notable_indicators: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ToolEvidence(BaseModel):
    """Auditable record of a model-selected tool invocation."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    output: Any
    status: Literal["success", "error"]
    latency_ms: int = Field(ge=0)


class SpecialistResult(BaseModel):
    destination: Literal["email_agent", "url_agent", "ip_agent", "file_agent"]
    assessment: SpecialistAssessment
    tool_evidence: list[ToolEvidence] = Field(default_factory=list)


class ThreatAnalysis(BaseModel):
    verdict: Literal["malicious", "suspicious", "benign", "unknown"]
    confidence: float = Field(ge=0, le=1)
    threat_type: str
    explanation: str
    evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    requires_human_approval: bool = False


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class IncidentReport(BaseModel):
    title: str
    summary: str
    severity: Literal["low", "medium", "high", "critical"]
    analysis: ThreatAnalysis
    approved: bool = False


class FinalizationResult(BaseModel):
    status: Literal["written", "not_approved", "not_requested"]
    output_path: str | None = None
