from __future__ import annotations

from pathlib import Path

from app.schemas import RiskProfile
from app.scoring import RiskScorer


def test_low_risk_profile_scores_in_approve_band() -> None:
    scorer = RiskScorer(Path("missing-model.pt"))
    score, risk_level, decision, probabilities, breakdown = scorer.score(
        RiskProfile(
            applicant_name="Jane Doe",
            coverage_amount=100000,
            deductible_amount=10000,
            prior_claims=0,
        )
    )

    assert score <= 35
    assert risk_level == "Low"
    assert decision == "Approve"
    assert probabilities.low > probabilities.high
    assert breakdown.factors


def test_high_risk_profile_scores_in_high_risk_band() -> None:
    scorer = RiskScorer(Path("missing-model.pt"))
    score, risk_level, decision, probabilities, _ = scorer.score(
        RiskProfile(
            coverage_amount=1500000,
            deductible_amount=0,
            prior_claims=5,
            missing_fields=["applicant_name", "policy_number", "coverage_type"],
            risk_indicators=["Fraud indicator mentioned", "Prior loss referenced"],
        )
    )

    assert score >= 66
    assert risk_level == "High"
    assert decision == "High Risk"
    assert probabilities.high > 0.35

