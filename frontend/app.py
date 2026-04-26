"""
QueryMind Streamlit UI — calls FastAPI only (no direct DB access).

Run: streamlit run frontend/app.py
"""

from __future__ import annotations

import os

import httpx
import streamlit as st

from api_client import DEFAULT_BASE, format_error_response, post_agent_query
from components import (
    csv_download_button,
    error_banner,
    results_table,
    schema_link_expander,
    sql_expander,
)

st.set_page_config(page_title="QueryMind", layout="wide")

st.title("QueryMind")
st.caption("Natural language → validated SQL (via FastAPI agent).")

with st.sidebar:
    st.subheader("Connection")
    api_base = st.text_input(
        "API base URL",
        value=os.environ.get("QUERYMIND_API_URL", DEFAULT_BASE),
        help="URL of the QueryMind FastAPI server (e.g. http://127.0.0.1:8000)",
    )
    max_rows = st.number_input("Max rows (optional)", min_value=1, max_value=10_000, value=500, step=1)

question = st.text_area(
    "Ask a question about your data",
    placeholder="Example: List all users who placed orders last month.",
    height=120,
)

run = st.button("Run query", type="primary")

if run and question.strip():
    with st.spinner("Running agent (MCP + Groq + validation)..."):
        try:
            data = post_agent_query(
                question.strip(),
                base_url=api_base,
                max_rows=int(max_rows),
            )
        except httpx.HTTPStatusError as exc:
            error_banner(format_error_response(exc.response))
        except httpx.RequestError as exc:
            error_banner(f"Could not reach API: {exc}")
        else:
            st.success("Query completed.")
            if data.get("warnings"):
                for w in data["warnings"]:
                    st.warning(w)
            sql_expander(data.get("final_sql", ""))
            schema_link_expander(data.get("schema_link", {}))
            if data.get("assumptions"):
                with st.expander("Assumptions", expanded=False):
                    for a in data["assumptions"]:
                        st.write(f"- {a}")
            cols = data.get("columns") or []
            rows = data.get("rows") or []
            results_table(cols, rows)
            st.caption(f"Execution time: {data.get('execution_time_ms', 0)} ms · Retries: {data.get('retries_used', 0)}")
            if cols and rows:
                csv_download_button(cols, rows, key="dl_csv")

elif run:
    st.warning("Enter a question first.")
