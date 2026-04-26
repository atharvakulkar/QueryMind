/* ===== Backend API Response Types (mirrors backend/schemas) ===== */

/** Schema linking output from the agent. */
export interface SchemaLink {
  tables: string[];
  columns: string[];
  join_hints: string[];
}

/** Successful agent run response from POST /api/v1/agent/query */
export interface AgentRunResponse {
  final_sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  execution_time_ms: number;
  retries_used: number;
  schema_link: SchemaLink;
  warnings: string[];
  assumptions: string[];
  insights: string | null;
}

/** Error envelope from the backend. */
export interface ApiErrorBody {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
}

/** Health endpoint response. */
export interface HealthResponse {
  status: string;
  app_name: string;
}

/** Readiness endpoint response. */
export interface ReadyResponse {
  status: string;
  database_reachable: boolean;
}

/* ===== NL Query Request ===== */
export interface HistoryEntry {
  role: 'user' | 'assistant';
  content: string;
}

export interface NLQueryRequest {
  question: string;
  max_rows?: number;
  dialect?: string;
  history?: HistoryEntry[];
}

/* ===== Frontend Message Types ===== */

export type MessageRole = 'user' | 'assistant';

export type ChartType = 'bar' | 'line' | 'area' | 'pie' | 'none';

/** A single message in the chat thread. */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;

  /* Agent response data (only present on assistant messages) */
  sql_query?: string;
  data_columns?: string[];
  data_rows?: Record<string, unknown>[];
  execution_time_ms?: number;
  retries_used?: number;
  schema_link?: SchemaLink;
  warnings?: string[];
  assumptions?: string[];
  chart_type?: ChartType;

  /* Loading / Error state */
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;

  /* LLM-generated insight (Phase 5) */
  insights?: string | null;
}

/** Sidebar history entry. */
export interface ChatSession {
  id: string;
  title: string;
  createdAt: Date;
  messageCount: number;
}

/** Connection status for the sidebar indicator. */
export type ConnectionStatus = 'connected' | 'disconnected' | 'checking';
