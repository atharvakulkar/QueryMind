import { type FC, useRef, useEffect, useState, useCallback } from 'react';
import { Send, Loader2, CornerDownLeft } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { cn } from '@/lib/utils';

export const ChatInput: FC = () => {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const isLoading = useChatStore((s) => s.isLoading);
  const connectionStatus = useChatStore((s) => s.connectionStatus);

  const canSend = value.trim().length > 0 && !isLoading && connectionStatus === 'connected';

  /** Auto-resize the textarea up to a max. */
  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  useEffect(() => {
    autoResize();
  }, [value, autoResize]);

  const handleSubmit = () => {
    if (!canSend) return;
    sendMessage(value.trim());
    setValue('');
    /* Reset height after send */
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-[var(--color-border-subtle)] bg-[var(--color-bg-secondary)]/80 backdrop-blur-sm px-4 md:px-8 lg:px-16 py-4">
      <div
        className={cn(
          'flex items-end gap-3 p-3 rounded-2xl glass-panel-elevated transition-all duration-200',
          canSend && 'glow-border',
        )}
      >
        <textarea
          ref={textareaRef}
          id="chat-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            connectionStatus !== 'connected'
              ? 'Waiting for backend connection…'
              : 'Ask a question about your data…'
          }
          disabled={connectionStatus !== 'connected'}
          rows={1}
          className="flex-1 bg-transparent text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-tertiary)]
            resize-none outline-none font-normal leading-relaxed max-h-[200px] disabled:opacity-50"
        />
        <div className="flex items-center gap-2 shrink-0">
          <span className="hidden md:flex items-center text-[10px] text-[var(--color-text-tertiary)] gap-1">
            <CornerDownLeft className="w-3 h-3" />
            Enter
          </span>
          <button
            onClick={handleSubmit}
            disabled={!canSend}
            id="send-button"
            className={cn(
              'p-2.5 rounded-xl transition-all duration-200',
              canSend
                ? 'bg-gradient-to-r from-[var(--color-brand-500)] to-[var(--color-accent-500)] text-white shadow-md hover:shadow-lg hover:shadow-[var(--color-brand-500)]/20 hover:scale-105 active:scale-95'
                : 'bg-[var(--color-bg-hover)] text-[var(--color-text-tertiary)] cursor-not-allowed',
            )}
            aria-label="Send message"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
      <p className="text-center text-[10px] text-[var(--color-text-tertiary)] mt-2">
        QueryMind generates read-only SQL. Always verify results before making business decisions.
      </p>
    </div>
  );
};
