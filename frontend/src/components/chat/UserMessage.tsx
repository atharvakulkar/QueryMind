import { type FC } from 'react';
import { User } from 'lucide-react';
import type { Message } from '@/types';
import { formatTime } from '@/lib/utils';

interface UserMessageProps {
  message: Message;
}

export const UserMessage: FC<UserMessageProps> = ({ message }) => {
  return (
    <div className="flex gap-3 py-4 max-w-4xl mx-auto">
      {/* Avatar */}
      <div className="shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-brand-500)] to-[var(--color-accent-500)] flex items-center justify-center shadow-sm">
        <User className="w-4 h-4 text-white" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-[var(--color-text-primary)]">You</span>
          <span className="text-[10px] text-[var(--color-text-tertiary)]">
            {formatTime(message.timestamp)}
          </span>
        </div>
        <p className="text-sm text-[var(--color-text-primary)] leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
      </div>
    </div>
  );
};
