from __future__ import annotations

from uuid import uuid4

from app.agents import RecommendationAgent
from app.config import Settings
from app.extraction import EntityExtractor
from app.ingestion import normalize_document, validate_upload
from app.layout import LayoutAnalyzer
from app.schemas import AnalysisResult
from app.scoring import RiskScorer
from app.storage import Storage


class AnalysisPipeline:
    def __init__(
        self,
        settings: Settings,
        storage: Storage,
        extractor: EntityExtractor | None = None,
        layout_analyzer: LayoutAnalyzer | None = None,
        scorer: RiskScorer | None = None,
        agent: RecommendationAgent | None = None,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.extractor = extractor or EntityExtractor()
        self.layout_analyzer = layout_analyzer or LayoutAnalyzer(settings)
        self.scorer = scorer or RiskScorer(settings.risk_model_path)
        self.agent = agent or RecommendationAgent(settings)

    def analyze(self, filename: str, content_type: str, file_bytes: bytes) -> AnalysisResult:
        validate_upload(filename, content_type, len(file_bytes), self.settings.max_upload_bytes)
        document_id = str(uuid4())
        storage_uri = self.storage.save_upload(document_id, filename, file_bytes)
        document = normalize_document(
            document_id=document_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(file_bytes),
            storage_uri=storage_uri,
            file_bytes=file_bytes,
        )
        document.layout_features = self.layout_analyzer.analyze(document)
        profile = self.extractor.extract(document)
        score, risk_level, decision, probabilities, breakdown = self.scorer.score(profile)
        recommendation = self.agent.recommend(profile, score, risk_level, decision, breakdown)

        result = AnalysisResult(
            document_id=document_id,
            risk_score=score,
            risk_level=risk_level,  # type: ignore[arg-type]
            decision=decision,  # type: ignore[arg-type]
            model_probabilities=probabilities,
            extracted_fields=profile,
            confidence_scores=profile.confidence_scores,
            missing_fields=profile.missing_fields,
            risk_factors=breakdown.factors,
            recommendation=recommendation,
            metadata=document.metadata,
        )
        self.storage.save_result(document_id, result.model_dump(mode="json"))
        return result

