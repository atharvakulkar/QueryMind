"""NL→SQL agent HTTP routes."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from backend.agent.agent_engine import QueryMindAgent
from backend.schemas.agent import AgentRunResponse, NLQueryRequest
from backend.dependencies import ConnectionManagerDep, SettingsDep
from mcp_server.client import McpSchemaClient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


def get_mcp_client(settings: SettingsDep) -> McpSchemaClient:
    return McpSchemaClient(settings)


def get_query_agent(
    settings: SettingsDep,
    connection_manager: ConnectionManagerDep,
    mcp_client: Annotated[McpSchemaClient, Depends(get_mcp_client)],
) -> QueryMindAgent:
    return QueryMindAgent(settings, connection_manager, mcp_client)


AgentDep = Annotated[QueryMindAgent, Depends(get_query_agent)]


@router.post("/agent/query", response_model=AgentRunResponse)
async def agent_query(
    body: NLQueryRequest,
    agent: AgentDep,
) -> AgentRunResponse:
    """Run the grounded NL→SQL agent (MCP + Groq + validation + retries)."""
    return await agent.run(body)
