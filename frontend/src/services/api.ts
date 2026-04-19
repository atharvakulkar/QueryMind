import axios from 'axios';
import type {
  AgentRunResponse,
  ApiErrorResponse,
  HealthResponse,
  NLQueryRequest,
  ReadyResponse,
} from '@/types';

/**
 * Axios instance pre-configured to use the Vite proxy.
 * In production you'd point this at your deployed backend URL.
 */
const apiClient = axios.create({
  baseURL: '/',
  timeout: 120_000, // agent queries can take time
  headers: {
    'Content-Type': 'application/json',
  },
});

/** Typed error extraction from Axios errors. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorResponse | undefined;
    if (data?.error?.message) {
      return data.error.message;
    }
    if (error.response?.status === 503) {
      return 'Service unavailable — check backend and database connectivity.';
    }
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. The query may be too complex.';
    }
    if (!error.response) {
      return 'Network error — unable to reach the backend server.';
    }
    return `Server error (${error.response.status}): ${error.response.statusText}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred.';
}

/* ===== API Functions ===== */

/** Check backend liveness. */
export async function checkHealth(): Promise<HealthResponse> {
  const res = await apiClient.get<HealthResponse>('/health');
  return res.data;
}

/** Check backend + database readiness. */
export async function checkReady(): Promise<ReadyResponse> {
  const res = await apiClient.get<ReadyResponse>('/ready');
  return res.data;
}

/** Send a natural-language query to the NL→SQL agent. */
export async function sendAgentQuery(
  request: NLQueryRequest,
): Promise<AgentRunResponse> {
  const res = await apiClient.post<AgentRunResponse>(
    '/api/v1/agent/query',
    request,
  );
  return res.data;
}

export default apiClient;
