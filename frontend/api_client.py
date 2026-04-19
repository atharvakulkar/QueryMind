"""HTTP client for QueryMind FastAPI backend."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE = os.environ.get("QUERYMIND_API_URL", "http://127.0.0.1:8000")


def post_agent_query(
    question: str,
    *,
    base_url: str = DEFAULT_BASE,
    max_rows: int | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """POST /api/v1/agent/query; returns JSON dict or raises httpx.HTTPError."""
    payload: dict[str, Any] = {"question": question}
    if max_rows is not None:
        payload["max_rows"] = max_rows
    url = base_url.rstrip("/") + "/api/v1/agent/query"
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def format_error_response(response: httpx.Response) -> str:
    """Parse FastAPI QueryMind error JSON if present."""
    try:
        data = response.json()
        err = data.get("error") or {}
        code = err.get("code", response.status_code)
        msg = err.get("message", response.text)
        return f"[{code}] {msg}"
    except Exception:
        return response.text or str(response.status_code)
