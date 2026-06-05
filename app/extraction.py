from __future__ import annotations

import re

from app.schemas import NormalizedDocument, RiskProfile


MONEY_RE = re.compile(r"(?:\$|USD\s*)\s*([0-9][0-9,]*(?:\.\d{1,2})?)", re.IGNORECASE)
POLICY_RE = re.compile(r"\b(?:policy\s*(?:number|no\.?)?[:#]?\s*)([A-Z0-9-]{5,})", re.IGNORECASE)
CLAIMS_RE = re.compile(r"\b(?:prior\s*)?claims?\s*(?:history)?[:#]?\s*(\d+)", re.IGNORECASE)
DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")


class EntityExtractor:
    def __init__(self) -> None:
        self._nlp = None
        try:
            import spacy

            self._nlp = spacy.blank("en")
        except Exception:
            self._nlp = None

    def extract(self, document: NormalizedDocument) -> RiskProfile:
        text = document.text or ""
        profile = RiskProfile()

        profile.applicant_name = _find_labeled_value(text, ["applicant name", "insured name", "name"])
        profile.policy_number = _first_group(POLICY_RE, text)
        profile.coverage_type = _find_labeled_value(
            text, ["coverage type", "policy type", "insurance type", "line of business"]
        )
        amounts = [_money_to_float(match) for match in MONEY_RE.findall(text)]
        if amounts:
            profile.coverage_amount = max(amounts)
            if len(amounts) > 1:
                profile.deductible_amount = min(amounts)
        claims = _first_group(CLAIMS_RE, text)
        if claims is not None:
            profile.prior_claims = int(claims)
        profile.claim_history = _find_labeled_value(text, ["claim history", "loss history"])
        profile.incident_dates = DATE_RE.findall(text)
        profile.property_details = _find_labeled_value(text, ["property details", "property"])
        profile.location_information = _find_labeled_value(
            text, ["location", "address", "risk location", "garaging address"]
        )
        profile.vehicle_information = _find_labeled_value(text, ["vehicle", "vin", "vehicle details"])
        profile.risk_indicators = _risk_indicators(text)

        fields = [
            "applicant_name",
            "policy_number",
            "coverage_type",
            "coverage_amount",
            "deductible_amount",
            "prior_claims",
            "location_information",
        ]
        for field in fields:
            value = getattr(profile, field)
            if value in (None, "", []):
                profile.missing_fields.append(field)
                profile.confidence_scores[field] = 0.0
            else:
                profile.confidence_scores[field] = 0.72 if field != "coverage_amount" else 0.82

        return profile


def _find_labeled_value(text: str, labels: list[str]) -> str | None:
    for label in labels:
        pattern = re.compile(
            rf"{re.escape(label)}\s*[:#-]\s*(?P<value>[^\n\r]+)",
            re.IGNORECASE,
        )
        match = pattern.search(text)
        if match:
            return match.group("value").strip()[:240]
    return None


def _first_group(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def _money_to_float(value: str) -> float:
    return float(value.replace(",", ""))


def _risk_indicators(text: str) -> list[str]:
    lowered = text.lower()
    indicators = []
    keywords = {
        "prior loss": "Prior loss referenced",
        "fraud": "Fraud indicator mentioned",
        "lapse": "Coverage lapse mentioned",
        "hazard": "Hazard indicator mentioned",
        "fire": "Fire exposure mentioned",
        "flood": "Flood exposure mentioned",
        "theft": "Theft exposure mentioned",
        "unverified": "Unverified information mentioned",
    }
    for keyword, label in keywords.items():
        if keyword in lowered:
            indicators.append(label)
    return indicators

