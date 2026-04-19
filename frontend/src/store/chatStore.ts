import { create } from 'zustand';
import type {
  ChatSession,
  ConnectionStatus,
  Message,
} from '@/types';
import {
  checkReady,
  extractErrorMessage,
  sendAgentQuery,
} from '@/services/api';
import { detectChartType, generateId } from '@/lib/utils';

/* ===== Store Shape ===== */
interface ChatState {
  /* Messages */
  messages: Message[];
  isLoading: boolean;

  /* Sessions */
  sessions: ChatSession[];
  activeSessionId: string | null;

  /* Connection */
  connectionStatus: ConnectionStatus;
  dbReachable: boolean;

  /* Sidebar */
  sidebarOpen: boolean;

  /* Toast */
  toasts: ToastItem[];

  /* Actions */
  sendMessage: (question: string) => Promise<void>;
  clearMessages: () => void;
  newSession: () => void;
  switchSession: (id: string) => void;
  checkConnection: () => Promise<void>;
  toggleSidebar: () => void;
  addToast: (toast: Omit<ToastItem, 'id'>) => void;
  removeToast: (id: string) => void;
}

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  variant: 'default' | 'destructive' | 'success';
}

/* ===== Session storage helpers ===== */
interface SessionData {
  session: ChatSession;
  messages: Message[];
}

function loadSessions(): Map<string, SessionData> {
  try {
    const raw = localStorage.getItem('querymind_sessions');
    if (!raw) return new Map();
    const parsed = JSON.parse(raw) as [string, SessionData][];
    return new Map(
      parsed.map(([id, data]) => [
        id,
        {
          ...data,
          session: {
            ...data.session,
            createdAt: new Date(data.session.createdAt),
          },
          messages: data.messages.map((m) => ({
            ...m,
            timestamp: new Date(m.timestamp),
          })),
        },
      ]),
    );
  } catch {
    return new Map();
  }
}

function saveSessions(sessions: Map<string, SessionData>): void {
  try {
    localStorage.setItem(
      'querymind_sessions',
      JSON.stringify(Array.from(sessions.entries())),
    );
  } catch {
    /* localStorage is best-effort */
  }
}

/* ===== Create store ===== */
export const useChatStore = create<ChatState>((set, get) => {
  const storedSessions = loadSessions();
  const sessionList = Array.from(storedSessions.values()).map((s) => s.session);
  const latestSession = sessionList.sort(
    (a, b) => b.createdAt.getTime() - a.createdAt.getTime(),
  )[0];

  const initialSessionId = latestSession?.id ?? null;
  const initialMessages = initialSessionId
    ? storedSessions.get(initialSessionId)?.messages ?? []
    : [];

  return {
    messages: initialMessages,
    isLoading: false,
    sessions: sessionList,
    activeSessionId: initialSessionId,
    connectionStatus: 'checking',
    dbReachable: false,
    sidebarOpen: true,
    toasts: [],

    sendMessage: async (question: string) => {
      const state = get();
      if (state.isLoading) return;

      /* Ensure we have an active session */
      let sessionId = state.activeSessionId;
      if (!sessionId) {
        sessionId = generateId();
        const newSession: ChatSession = {
          id: sessionId,
          title: question.slice(0, 60),
          createdAt: new Date(),
          messageCount: 0,
        };
        set((s) => ({
          activeSessionId: sessionId,
          sessions: [newSession, ...s.sessions],
        }));
      }

      /* Create user message */
      const userMsg: Message = {
        id: generateId(),
        role: 'user',
        content: question,
        timestamp: new Date(),
      };

      /* Create placeholder assistant message */
      const assistantPlaceholder: Message = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isLoading: true,
      };

      set((s) => ({
        messages: [...s.messages, userMsg, assistantPlaceholder],
        isLoading: true,
      }));

      try {
        const response = await sendAgentQuery({ question });

        const chartType = detectChartType(response.columns, response.rows);

        const assistantMsg: Message = {
          ...assistantPlaceholder,
          content: `Query executed successfully in ${response.execution_time_ms}ms — returned ${response.rows.length} row(s).`,
          isLoading: false,
          sql_query: response.final_sql,
          data_columns: response.columns,
          data_rows: response.rows,
          execution_time_ms: response.execution_time_ms,
          retries_used: response.retries_used,
          schema_link: response.schema_link,
          warnings: response.warnings,
          assumptions: response.assumptions,
          chart_type: chartType,
        };

        set((s) => {
          const updatedMessages = s.messages.map((m) =>
            m.id === assistantPlaceholder.id ? assistantMsg : m,
          );

          /* Persist */
          const allSessions = loadSessions();
          const finalSessionId = sessionId!;
          allSessions.set(finalSessionId, {
            session: {
              id: finalSessionId,
              title:
                allSessions.get(finalSessionId)?.session.title ??
                question.slice(0, 60),
              createdAt:
                allSessions.get(finalSessionId)?.session.createdAt ??
                new Date(),
              messageCount: updatedMessages.length,
            },
            messages: updatedMessages,
          });
          saveSessions(allSessions);

          return {
            messages: updatedMessages,
            isLoading: false,
            sessions: s.sessions.map((sess) =>
              sess.id === finalSessionId
                ? { ...sess, messageCount: updatedMessages.length }
                : sess,
            ),
          };
        });
      } catch (error) {
        const errorMessage = extractErrorMessage(error);

        const errorMsg: Message = {
          ...assistantPlaceholder,
          content: errorMessage,
          isLoading: false,
          isError: true,
          errorMessage,
        };

        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === assistantPlaceholder.id ? errorMsg : m,
          ),
          isLoading: false,
        }));

        get().addToast({
          title: 'Query Failed',
          description: errorMessage,
          variant: 'destructive',
        });
      }
    },

    clearMessages: () => {
      const { activeSessionId } = get();
      set({ messages: [] });
      if (activeSessionId) {
        const allSessions = loadSessions();
        allSessions.delete(activeSessionId);
        saveSessions(allSessions);
      }
      set((s) => ({
        sessions: s.sessions.filter((sess) => sess.id !== s.activeSessionId),
        activeSessionId: null,
      }));
    },

    newSession: () => {
      set({
        messages: [],
        activeSessionId: null,
      });
    },

    switchSession: (id: string) => {
      const allSessions = loadSessions();
      const data = allSessions.get(id);
      set({
        activeSessionId: id,
        messages: data?.messages ?? [],
      });
    },

    checkConnection: async () => {
      set({ connectionStatus: 'checking' });
      try {
        const result = await checkReady();
        set({
          connectionStatus: 'connected',
          dbReachable: result.database_reachable,
        });
      } catch {
        set({ connectionStatus: 'disconnected', dbReachable: false });
      }
    },

    toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

    addToast: (toast) => {
      const id = generateId();
      set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }));
      setTimeout(() => get().removeToast(id), 5000);
    },

    removeToast: (id) =>
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  };
});
