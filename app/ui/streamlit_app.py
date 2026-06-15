from __future__ import annotations

import os
from pathlib import Path
import sys

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.pipeline import AnalysisPipeline  # noqa: E402
from app.storage import build_storage  # noqa: E402


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Insurance Risk Analyzer", layout="wide")
st.title("Insurance Document Risk Analyzer")

with st.sidebar:
    st.header("Service")
    api_base_url = st.text_input("API base URL", API_BASE_URL)
    if st.button("Check health"):
        try:
            response = requests.get(f"{api_base_url}/health", timeout=10)
            st.json(response.json())
        except Exception as exc:
            st.error(f"Health check failed: {exc}")

uploaded = st.file_uploader("Upload an insurance PDF or image", type=["pdf", "png", "jpg", "jpeg"])

if uploaded is not None and st.button("Analyze document", type="primary"):
    content = uploaded.getvalue()
    files = {"file": (uploaded.name, content, uploaded.type)}
    with st.spinner("Analyzing document..."):
        try:
            response = requests.post(f"{api_base_url}/analyze", files=files, timeout=120)
            response.raise_for_status()
            result = response.json()
        except Exception as exc:
            st.info(f"API unavailable, running local Streamlit analysis instead. Details: {exc}")
            settings = get_settings()
            pipeline = AnalysisPipeline(settings=settings, storage=build_storage(settings))
            result = pipeline.analyze(uploaded.name, uploaded.type or "", content).model_dump(mode="json")

    col_score, col_decision, col_id = st.columns(3)
    col_score.metric("Risk score", result["risk_score"])
    col_decision.metric("Decision", result["decision"])
    col_id.caption(f"Document ID: {result['document_id']}")

    st.subheader("Model probabilities")
    st.bar_chart(result["model_probabilities"])

    left, right = st.columns(2)
    with left:
        st.subheader("Extracted fields")
        fields = result["extracted_fields"]
        st.json(fields)
    with right:
        st.subheader("Risk factors")
        for factor in result["risk_factors"]:
            st.write(f"- {factor}")
        st.subheader("Missing fields")
        if result["missing_fields"]:
            for field in result["missing_fields"]:
                st.write(f"- {field}")
        else:
            st.write("No critical missing fields detected.")

    st.subheader("Recommendation")
    st.write(result["recommendation"]["summary"])
    st.write("Suggested actions")
    for action in result["recommendation"]["suggested_actions"]:
        st.write(f"- {action}")

    with st.expander("Raw analysis JSON"):
        st.json(result)
