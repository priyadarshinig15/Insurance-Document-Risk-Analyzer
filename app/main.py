from __future__ import annotations

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile

from app.config import Settings, get_settings
from app.ingestion import ValidationError
from app.pipeline import AnalysisPipeline
from app.schemas import AnalysisResult, HealthResponse
from app.storage import StorageError, build_storage

app = FastAPI(
    title="Insurance Document Risk Analyzer",
    version="0.1.0",
    description="Extracts insurance risk fields, scores underwriting risk, and returns recommendations.",
)


def get_pipeline(settings: Settings = Depends(get_settings)) -> AnalysisPipeline:
    try:
        storage = build_storage(settings)
    except StorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AnalysisPipeline(settings=settings, storage=storage)


@app.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    try:
        pipeline = get_pipeline(settings)
        storage_ready = pipeline.storage.ready()
        llm_ready = pipeline.agent.ready()
        model_ready = pipeline.scorer.ready()
        layout_ready = pipeline.layout_analyzer.ready()
    except Exception:
        return HealthResponse(
            status="degraded",
            storage_backend=settings.storage_backend,
            storage_ready=False,
            llm_provider=settings.llm_provider,
            llm_ready=False,
            risk_model_ready=False,
            layoutlm_enabled=settings.layoutlm_enabled,
        )
    return HealthResponse(
        status="ok" if storage_ready and llm_ready and model_ready and layout_ready else "degraded",
        storage_backend=settings.storage_backend,
        storage_ready=storage_ready,
        llm_provider=settings.llm_provider,
        llm_ready=llm_ready,
        risk_model_ready=model_ready,
        layoutlm_enabled=settings.layoutlm_enabled,
    )


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_document(
    file: UploadFile = File(...),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> AnalysisResult:
    content = await file.read()
    try:
        return pipeline.analyze(file.filename or "upload", file.content_type or "", content)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/document/{document_id}", response_model=AnalysisResult)
def get_document(document_id: str, pipeline: AnalysisPipeline = Depends(get_pipeline)) -> AnalysisResult:
    try:
        return AnalysisResult.model_validate(pipeline.storage.get_result(document_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document analysis was not found") from exc

