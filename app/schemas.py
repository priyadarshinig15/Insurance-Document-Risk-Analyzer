from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["Low", "Medium", "High"]
Decision = Literal["Approve", "Manual Review", "High Risk"]


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    page_count: int = 0
    storage_uri: str
    warnings: list[str] = Field(default_factory=list)


class NormalizedDocument(BaseModel):
    metadata: DocumentMetadata
    text: str = ""
    pages: list[str] = Field(default_factory=list)
    layout_features: dict[str, Any] = Field(default_factory=dict)


class RiskProfile(BaseModel):
    applicant_name: str | None = None
    policy_number: str | None = None
    coverage_type: str | None = None
    coverage_amount: float | None = None
    deductible_amount: float | None = None
    prior_claims: int | None = None
    claim_history: str | None = None
    incident_dates: list[str] = Field(default_factory=list)
    property_details: str | None = None
    location_information: str | None = None
    vehicle_information: str | None = None
    risk_indicators: list[str] = Field(default_factory=list)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)


class ModelProbabilities(BaseModel):
    low: float
    medium: float
    high: float


class ScoreBreakdown(BaseModel):
    features: dict[str, float] = Field(default_factory=dict)
    factors: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    summary: str
    suggested_actions: list[str] = Field(default_factory=list)
    inconsistencies: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    document_id: str
    risk_score: int
    risk_level: RiskLevel
    decision: Decision
    model_probabilities: ModelProbabilities
    extracted_fields: RiskProfile
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    recommendation: Recommendation
    metadata: DocumentMetadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    storage_backend: str
    storage_ready: bool
    llm_provider: str
    llm_ready: bool
    risk_model_ready: bool
    layoutlm_enabled: bool
