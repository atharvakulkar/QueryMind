import { type FC, useRef, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';
import { UserMessage } from '@/components/chat/UserMessage';
import { AssistantMessage } from '@/components/chat/AssistantMessage';
import { WelcomeScreen } from '@/components/chat/WelcomeScreen';

export const MessageList: FC = () => {
  const messages = useChatStore((s) => s.messages);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return <WelcomeScreen />;
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-8 lg:px-16 py-6 space-y-1">
      {messages.map((msg, idx) => (
        <div
          key={msg.id}
          className="animate-fade-in"
          style={{ animationDelay: `${Math.min(idx * 30, 300)}ms` }}
        >
          {msg.role === 'user' ? (
            <UserMessage message={msg} />
          ) : (
            <AssistantMessage message={msg} />
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};
