"""Reusable Streamlit UI helpers."""

from __future__ import annotations

import csv
import io
from typing import Any

import streamlit as st


def error_banner(message: str) -> None:
    st.error(message)


def sql_expander(sql: str) -> None:
    with st.expander("Generated SQL", expanded=False):
        st.code(sql, language="sql")


def schema_link_expander(link: dict[str, Any]) -> None:
    with st.expander("Schema link (tables & columns)", expanded=False):
        st.json(link)


def results_table(columns: list[str], rows: list[dict[str, Any]]) -> None:
    if not columns and not rows:
        st.info("No rows returned.")
        return
    st.dataframe(
        [{c: r.get(c) for c in columns} for r in rows],
        use_container_width=True,
    )


def csv_download_button(columns: list[str], rows: list[dict[str, Any]], key: str) -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k) for k in columns})
    st.download_button(
        label="Download CSV",
        data=buf.getvalue().encode("utf-8"),
        file_name="querymind_results.csv",
        mime="text/csv",
        key=key,
    )
