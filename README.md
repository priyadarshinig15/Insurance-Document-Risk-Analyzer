# Insurance Document Risk Analyzer

An API-first underwriting automation demo that ingests insurance PDFs/images, extracts structured risk fields, scores underwriting risk, and generates analyst-ready recommendations.

## What is included

- FastAPI backend with `POST /analyze`, `GET /document/{id}`, and `GET /health`.
- Local storage by default, with an S3 adapter for AWS deployments.
- Document validation and text extraction for PDFs/images with graceful local fallbacks.
- LayoutLMv3 adapter hook for layout-aware processing.
- spaCy/regex entity extraction into a validated risk profile.
- LangChain-compatible recommendation layer with offline, OpenAI, and Anthropic provider modes.
- PyTorch classifier hook with deterministic fallback scoring when no trained artifact is available.
- Streamlit analyst UI.
- Docker and GitHub Actions CI scaffolding.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open the API docs at `http://127.0.0.1:8000/docs`.

Run the demo UI:

```powershell
streamlit run app/ui/streamlit_app.py
```

## Configuration

Copy `.env.example` to `.env` and set values as needed. The service can run in `offline` LLM mode and `local` storage mode without cloud or model credentials.

For AWS deployment:

- Set `STORAGE_BACKEND=s3`
- Set `S3_BUCKET`
- Provide AWS credentials through the runtime environment

## Model path

`scripts/train_model.py` creates a small PyTorch classifier artifact from CSV data. The expected CSV columns are:

- `prior_claims`
- `claim_severity`
- `coverage_amount`
- `geographic_risk`
- `missing_fields`
- `risk_label` with values `low`, `medium`, or `high`

When no artifact is present, the service uses a transparent fallback scoring model so the pipeline remains demoable.

