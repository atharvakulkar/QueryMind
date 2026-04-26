import { type FC } from 'react';
import { useChatStore } from '@/store/chatStore';
import { Database, Sparkles, Table2, BrainCircuit, Upload } from 'lucide-react';
import { DatasetUpload } from '@/components/upload/DatasetUpload';

const SUGGESTIONS = [
  'Show me the top 10 customers by revenue',
  'What are the total sales per month this year?',
  'List all products with inventory below 50 units',
  'Compare revenue across all regions',
];

export const WelcomeScreen: FC = () => {
  const sendMessage = useChatStore((s) => s.sendMessage);

  return (
    <div className="flex-1 flex items-center justify-center px-6 py-12">
      <div className="max-w-2xl w-full text-center space-y-8">
        {/* Logo mark */}
        <div className="flex justify-center">
          <div className="relative">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[var(--color-brand-500)] to-[var(--color-accent-500)] flex items-center justify-center shadow-xl shadow-[var(--color-brand-500)]/20">
              <BrainCircuit className="w-10 h-10 text-white" />
            </div>
            <div className="absolute -inset-1 rounded-2xl bg-gradient-to-br from-[var(--color-brand-500)] to-[var(--color-accent-500)] opacity-20 blur-lg -z-10" />
          </div>
        </div>

        {/* Title */}
        <div className="space-y-3">
          <h1 className="text-3xl font-bold tracking-tight">
            <span className="gradient-text">QueryMind</span>
          </h1>
          <p className="text-[var(--color-text-secondary)] text-base max-w-md mx-auto leading-relaxed">
            Ask questions in plain English. Get SQL-powered insights instantly.
            Your enterprise database, conversational.
          </p>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-3">
          {[
            { icon: Database, label: 'Schema Aware' },
            { icon: Sparkles, label: 'AI-Powered' },
            { icon: Table2, label: 'Instant Tables' },
            { icon: Upload, label: 'Upload CSV' },
          ].map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-2 px-3.5 py-2 rounded-full glass-panel-elevated text-xs font-medium text-[var(--color-text-secondary)]"
            >
              <Icon className="w-3.5 h-3.5 text-[var(--color-brand-400)]" />
              {label}
            </div>
          ))}
        </div>

        {/* Suggestion cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          {SUGGESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              className="text-left p-4 rounded-xl glass-panel-elevated
                hover:border-[var(--color-border-brand)] hover:shadow-[var(--shadow-glow)]
                transition-all duration-200 group"
            >
              <p className="text-sm text-[var(--color-text-secondary)] group-hover:text-[var(--color-text-primary)] transition-colors duration-200 leading-relaxed">
                {q}
              </p>
            </button>
          ))}
        </div>

        {/* Upload Zone */}
        <div className="pt-6 border-t border-[var(--color-border-subtle)]/50 mt-8">
          <DatasetUpload />
        </div>
      </div>
    </div>
  );
};
