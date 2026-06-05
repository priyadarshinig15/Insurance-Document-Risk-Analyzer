from __future__ import annotations

import os

from app.config import Settings
from app.schemas import Recommendation, RiskProfile, ScoreBreakdown


class RecommendationAgent:
    def __init__(self, settings: Settings):
        self.provider = settings.llm_provider
        self.model = settings.llm_model

    def ready(self) -> bool:
        if self.provider == "offline":
            return True
        if self.provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        if self.provider == "anthropic":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        return False

    def recommend(
        self,
        profile: RiskProfile,
        score: int,
        risk_level: str,
        decision: str,
        breakdown: ScoreBreakdown,
    ) -> Recommendation:
        if self.provider in {"openai", "anthropic"} and self.ready():
            generated = self._try_llm(profile, score, risk_level, decision, breakdown)
            if generated:
                return generated
        return self._offline_recommendation(profile, score, risk_level, decision, breakdown)

    def _try_llm(
        self,
        profile: RiskProfile,
        score: int,
        risk_level: str,
        decision: str,
        breakdown: ScoreBreakdown,
    ) -> Recommendation | None:
        prompt = (
            "You are an underwriting assistant. Generate a concise insurance underwriting "
            "recommendation using the extracted profile, score, and factors. "
            "Return plain text summary and three suggested actions.\n"
            f"Risk level: {risk_level}\nDecision: {decision}\nScore: {score}\n"
            f"Profile: {profile.model_dump()}\nFactors: {breakdown.factors}\n"
        )
        try:
            if self.provider == "openai":
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(model=self.model or "gpt-4o-mini", temperature=0.1)
                content = llm.invoke(prompt).content
            else:
                from langchain_anthropic import ChatAnthropic

                llm = ChatAnthropic(model=self.model or "claude-3-5-sonnet-latest", temperature=0.1)
                content = llm.invoke(prompt).content
        except Exception:
            return None

        return Recommendation(
            summary=str(content)[:1500],
            suggested_actions=_default_actions(profile, decision),
            inconsistencies=_detect_inconsistencies(profile),
        )

    def _offline_recommendation(
        self,
        profile: RiskProfile,
        score: int,
        risk_level: str,
        decision: str,
        breakdown: ScoreBreakdown,
    ) -> Recommendation:
        factor_text = "; ".join(breakdown.factors)
        summary = (
            f"The document is classified as {risk_level.lower()} risk with a score of {score}. "
            f"Recommended decision: {decision}. Key drivers: {factor_text}."
        )
        if profile.missing_fields:
            summary += " Additional verification is recommended because critical fields are missing."
        return Recommendation(
            summary=summary,
            suggested_actions=_default_actions(profile, decision),
            inconsistencies=_detect_inconsistencies(profile),
        )


def _default_actions(profile: RiskProfile, decision: str) -> list[str]:
    actions = []
    if profile.missing_fields:
        actions.append("Request missing underwriting information from the applicant or broker.")
    if profile.prior_claims and profile.prior_claims > 0:
        actions.append("Verify loss history and claim severity before binding.")
    if decision != "Approve":
        actions.append("Route to a human underwriter for review.")
    if not actions:
        actions.append("Proceed with standard underwriting review.")
    return actions


def _detect_inconsistencies(profile: RiskProfile) -> list[str]:
    inconsistencies = []
    if (
        profile.coverage_amount is not None
        and profile.deductible_amount is not None
        and profile.deductible_amount > profile.coverage_amount
    ):
        inconsistencies.append("Deductible amount exceeds coverage amount.")
    if profile.prior_claims == 0 and profile.claim_history and "loss" in profile.claim_history.lower():
        inconsistencies.append("Claim history references losses but prior_claims is zero.")
    return inconsistencies

