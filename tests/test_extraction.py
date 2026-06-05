from __future__ import annotations

from app.extraction import EntityExtractor
from app.schemas import DocumentMetadata, NormalizedDocument


def test_extracts_core_insurance_fields() -> None:
    document = NormalizedDocument(
        metadata=DocumentMetadata(
            document_id="doc-1",
            filename="sample.pdf",
            content_type="application/pdf",
            size_bytes=100,
            storage_uri="local",
        ),
        text="""
        Applicant Name: John Doe
        Policy Number: PROP-12345
        Coverage Type: Property Insurance
        Coverage Amount: $500,000
        Deductible Amount: $10,000
        Claims: 2
        Location: 10 Main Street
        Flood exposure noted.
        """,
    )

    profile = EntityExtractor().extract(document)

    assert profile.applicant_name == "John Doe"
    assert profile.policy_number == "PROP-12345"
    assert profile.coverage_type == "Property Insurance"
    assert profile.coverage_amount == 500000
    assert profile.deductible_amount == 10000
    assert profile.prior_claims == 2
    assert "Flood exposure mentioned" in profile.risk_indicators

