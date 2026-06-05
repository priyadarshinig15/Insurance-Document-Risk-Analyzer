from __future__ import annotations

import os

import requests
import streamlit as st


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
    files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
    with st.spinner("Analyzing document..."):
        try:
            response = requests.post(f"{api_base_url}/analyze", files=files, timeout=120)
        except Exception as exc:
            st.error(f"Request failed: {exc}")
            st.stop()
    if response.status_code >= 400:
        st.error(response.text)
        st.stop()
    result = response.json()

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

