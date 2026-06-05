from __future__ import annotations

import math
from pathlib import Path

from app.schemas import ModelProbabilities, RiskProfile, ScoreBreakdown


class RiskScorer:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._torch_model = None
        self._torch = None
        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            return
        try:
            import torch

            self._torch = torch
            self._torch_model = torch.jit.load(str(self.model_path))
            self._torch_model.eval()
        except Exception:
            self._torch = None
            self._torch_model = None

    def ready(self) -> bool:
        return self._torch_model is not None or not self.model_path.exists()

    def score(self, profile: RiskProfile) -> tuple[int, str, str, ModelProbabilities, ScoreBreakdown]:
        features = engineer_features(profile)
        if self._torch_model is not None and self._torch is not None:
            probabilities = self._score_with_torch(features)
        else:
            probabilities = self._score_with_fallback(features)

        score = round((probabilities.medium * 50) + (probabilities.high * 100))
        if score <= 35:
            risk_level = "Low"
            decision = "Approve"
        elif score <= 65:
            risk_level = "Medium"
            decision = "Manual Review"
        else:
            risk_level = "High"
            decision = "High Risk"

        factors = _factor_labels(features, profile)
        return score, risk_level, decision, probabilities, ScoreBreakdown(features=features, factors=factors)

    def _score_with_torch(self, features: dict[str, float]) -> ModelProbabilities:
        tensor = self._torch.tensor([_feature_vector(features)], dtype=self._torch.float32)
        with self._torch.no_grad():
            logits = self._torch_model(tensor)
            probs = self._torch.softmax(logits, dim=1)[0].tolist()
        return ModelProbabilities(low=probs[0], medium=probs[1], high=probs[2])

    def _score_with_fallback(self, features: dict[str, float]) -> ModelProbabilities:
        raw = (
            features["prior_claims_norm"] * 1.25
            + features["coverage_norm"] * 0.85
            + features["missing_fields_norm"] * 0.65
            + features["risk_indicator_norm"] * 0.95
            + features["deductible_inverse_norm"] * 0.25
        )
        high = _sigmoid(raw - 1.75)
        medium = max(0.03, 0.55 - abs(raw - 1.15) * 0.40)
        low = max(0.03, 1 - high - medium)
        total = low + medium + high
        return ModelProbabilities(low=low / total, medium=medium / total, high=high / total)


def engineer_features(profile: RiskProfile) -> dict[str, float]:
    coverage = profile.coverage_amount or 0.0
    deductible = profile.deductible_amount or 0.0
    prior_claims = profile.prior_claims or 0
    missing = len(profile.missing_fields)
    indicators = len(profile.risk_indicators)
    return {
        "prior_claims_norm": min(prior_claims / 5, 1.0),
        "coverage_norm": min(coverage / 1_000_000, 1.0),
        "missing_fields_norm": min(missing / 7, 1.0),
        "risk_indicator_norm": min(indicators / 5, 1.0),
        "deductible_inverse_norm": 1.0 if deductible == 0 else max(0.0, 1 - min(deductible / 25_000, 1.0)),
    }


def _feature_vector(features: dict[str, float]) -> list[float]:
    return [
        features["prior_claims_norm"],
        features["coverage_norm"],
        features["missing_fields_norm"],
        features["risk_indicator_norm"],
        features["deductible_inverse_norm"],
    ]


def _factor_labels(features: dict[str, float], profile: RiskProfile) -> list[str]:
    labels = []
    if features["prior_claims_norm"] > 0:
        labels.append(f"{profile.prior_claims} prior claim(s) identified")
    if features["coverage_norm"] >= 0.5:
        labels.append("High requested coverage amount")
    if profile.missing_fields:
        labels.append(f"Missing critical fields: {', '.join(profile.missing_fields)}")
    labels.extend(profile.risk_indicators)
    if not labels:
        labels.append("No major adverse risk factors detected")
    return labels


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))
