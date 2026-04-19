import { useEffect, useState, type FC } from 'react';
import {
  Database,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
  Trash2,
  Wifi,
  WifiOff,
  Loader2,
  Zap,
  Clock,
} from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { cn, truncate } from '@/lib/utils';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { ToastContainer } from '@/components/ui/ToastContainer';

export const MainLayout: FC = () => {
  const {
    sidebarOpen,
    toggleSidebar,
    connectionStatus,
    dbReachable,
    sessions,
    activeSessionId,
    checkConnection,
    newSession,
    clearMessages,
    switchSession,
    messages,
  } = useChatStore();

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    checkConnection();
    const interval = setInterval(checkConnection, 30_000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  if (!mounted) return null;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--color-bg-primary)]">
      {/* ===== Sidebar ===== */}
      <aside
        className={cn(
          'flex flex-col h-full transition-all duration-300 ease-in-out glass-panel border-r border-[var(--color-border-subtle)]',
          sidebarOpen ? 'w-72 min-w-[288px]' : 'w-0 min-w-0 overflow-hidden',
        )}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border-subtle)]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-[var(--color-brand-500)] to-[var(--color-accent-500)]">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight text-[var(--color-text-primary)]">
                QueryMind
              </h1>
              <p className="text-[10px] font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">
                AI SQL Agent
              </p>
            </div>
          </div>
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-md hover:bg-[var(--color-bg-hover)] text-[var(--color-text-secondary)] transition-colors duration-150"
            aria-label="Close sidebar"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={newSession}
            id="new-chat-button"
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium
              bg-gradient-to-r from-[var(--color-brand-600)] to-[var(--color-accent-600)]
              text-white hover:from-[var(--color-brand-500)] hover:to-[var(--color-accent-500)]
              transition-all duration-200 shadow-md hover:shadow-lg hover:shadow-[var(--color-brand-500)]/20"
          >
            <MessageSquarePlus className="w-4 h-4" />
            New Chat
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-2 py-1">
          <p className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-tertiary)]">
            History
          </p>
          {sessions.length === 0 ? (
            <p className="px-3 py-6 text-xs text-center text-[var(--color-text-tertiary)]">
              No conversations yet
            </p>
          ) : (
            <div className="flex flex-col gap-0.5">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => switchSession(session.id)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-lg text-sm transition-all duration-150 group',
                    activeSessionId === session.id
                      ? 'bg-[var(--color-bg-active)] text-[var(--color-text-primary)] border border-[var(--color-border-brand)]'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]',
                  )}
                >
                  <span className="block truncate font-medium text-[13px]">
                    {truncate(session.title, 32)}
                  </span>
                  <span className="flex items-center gap-1 text-[10px] text-[var(--color-text-tertiary)] mt-0.5">
                    <Clock className="w-3 h-3" />
                    {session.messageCount} messages
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Footer — Status */}
        <div className="p-3 border-t border-[var(--color-border-subtle)]">
          {/* Connection Status */}
          <div className="flex items-center gap-2 px-2 py-1.5">
            {connectionStatus === 'connected' ? (
              <Wifi className="w-3.5 h-3.5 text-[var(--color-success)]" />
            ) : connectionStatus === 'checking' ? (
              <Loader2 className="w-3.5 h-3.5 text-[var(--color-warning)] animate-spin" />
            ) : (
              <WifiOff className="w-3.5 h-3.5 text-[var(--color-error)]" />
            )}
            <span className="text-xs text-[var(--color-text-secondary)]">
              {connectionStatus === 'connected'
                ? 'Backend Online'
                : connectionStatus === 'checking'
                  ? 'Checking…'
                  : 'Backend Offline'}
            </span>
          </div>

          {/* DB Status */}
          <div className="flex items-center gap-2 px-2 py-1.5">
            <Database
              className={cn(
                'w-3.5 h-3.5',
                dbReachable
                  ? 'text-[var(--color-success)]'
                  : 'text-[var(--color-text-tertiary)]',
              )}
            />
            <span className="text-xs text-[var(--color-text-secondary)]">
              {dbReachable ? 'Database Connected' : 'Database Unknown'}
            </span>
          </div>

          {/* Clear Chat */}
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className="w-full flex items-center justify-center gap-1.5 mt-2 px-3 py-2 rounded-lg text-xs
                text-[var(--color-error)] hover:bg-[var(--color-error)]/10 transition-colors duration-150"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear Chat
            </button>
          )}
        </div>
      </aside>

      {/* ===== Main Chat Area ===== */}
      <main className="flex-1 flex flex-col h-full min-w-0 relative">
        {/* Top Bar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-[var(--color-border-subtle)] glass-panel z-10">
          {!sidebarOpen && (
            <button
              onClick={toggleSidebar}
              className="p-1.5 rounded-md hover:bg-[var(--color-bg-hover)] text-[var(--color-text-secondary)] transition-colors duration-150"
              aria-label="Open sidebar"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          )}
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">
              {activeSessionId
                ? truncate(
                    sessions.find((s) => s.id === activeSessionId)?.title ?? 'Chat',
                    50,
                  )
                : 'New Conversation'}
            </h2>
            <span
              className={cn(
                'inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium',
                connectionStatus === 'connected'
                  ? 'bg-[var(--color-success)]/10 text-[var(--color-success)]'
                  : 'bg-[var(--color-error)]/10 text-[var(--color-error)]',
              )}
            >
              {connectionStatus === 'connected' ? 'Live' : 'Offline'}
            </span>
          </div>
        </header>

        {/* Messages */}
        <MessageList />

        {/* Input */}
        <ChatInput />
      </main>

      {/* Toast Notifications */}
      <ToastContainer />
    </div>
  );
};
