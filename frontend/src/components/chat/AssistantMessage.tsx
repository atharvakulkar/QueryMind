import { type FC } from 'react';
import { BrainCircuit, AlertTriangle, Clock, RotateCcw } from 'lucide-react';
import type { Message } from '@/types';
import { formatDuration, formatTime } from '@/lib/utils';
import { ThoughtProcessAccordion } from '@/components/chat/ThoughtProcessAccordion';
import { DynamicDataTable } from '@/components/data/DynamicDataTable';
import { DataChart } from '@/components/data/DataChart';
import { SkeletonLoader } from '@/components/ui/SkeletonLoader';

interface AssistantMessageProps {
  message: Message;
}

export const AssistantMessage: FC<AssistantMessageProps> = ({ message }) => {
  if (message.isLoading) {
    return (
      <div className="flex gap-3 py-4 max-w-4xl mx-auto">
        <div className="shrink-0 w-8 h-8 rounded-lg bg-[var(--color-bg-elevated)] border border-[var(--color-border-subtle)] flex items-center justify-center">
          <BrainCircuit className="w-4 h-4 text-[var(--color-brand-400)]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-[var(--color-text-brand)]">QueryMind</span>
            <span className="text-[10px] text-[var(--color-text-tertiary)]">Thinking…</span>
          </div>
          <SkeletonLoader />
        </div>
      </div>
    );
  }

  if (message.isError) {
    return (
      <div className="flex gap-3 py-4 max-w-4xl mx-auto">
        <div className="shrink-0 w-8 h-8 rounded-lg bg-[var(--color-error)]/10 border border-[var(--color-error)]/20 flex items-center justify-center">
          <AlertTriangle className="w-4 h-4 text-[var(--color-error)]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-[var(--color-error)]">Error</span>
            <span className="text-[10px] text-[var(--color-text-tertiary)]">
              {formatTime(message.timestamp)}
            </span>
          </div>
          <div className="p-3 rounded-lg bg-[var(--color-error)]/5 border border-[var(--color-error)]/10">
            <p className="text-sm text-[var(--color-error)] leading-relaxed">
              {message.errorMessage ?? message.content}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 py-4 max-w-4xl mx-auto">
      {/* Avatar */}
      <div className="shrink-0 w-8 h-8 rounded-lg bg-[var(--color-bg-elevated)] border border-[var(--color-border-subtle)] flex items-center justify-center">
        <BrainCircuit className="w-4 h-4 text-[var(--color-brand-400)]" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[var(--color-text-brand)]">QueryMind</span>
          <span className="text-[10px] text-[var(--color-text-tertiary)]">
            {formatTime(message.timestamp)}
          </span>
          {message.execution_time_ms != null && (
            <span className="inline-flex items-center gap-1 text-[10px] text-[var(--color-text-tertiary)]">
              <Clock className="w-3 h-3" />
              {formatDuration(message.execution_time_ms)}
            </span>
          )}
          {(message.retries_used ?? 0) > 0 && (
            <span className="inline-flex items-center gap-1 text-[10px] text-[var(--color-warning)]">
              <RotateCcw className="w-3 h-3" />
              {message.retries_used} retry
            </span>
          )}
        </div>

        {/* Summary */}
        <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
          {message.content}
        </p>

        {/* Warnings */}
        {message.warnings && message.warnings.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.warnings.map((w, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium bg-[var(--color-warning)]/10 text-[var(--color-warning)]"
              >
                <AlertTriangle className="w-3 h-3" />
                {w}
              </span>
            ))}
          </div>
        )}

        {/* Thought Process Accordion */}
        {(message.sql_query || message.schema_link) && (
          <ThoughtProcessAccordion message={message} />
        )}

        {/* Data Table */}
        {message.data_columns && message.data_rows && message.data_rows.length > 0 && (
          <DynamicDataTable
            columns={message.data_columns}
            rows={message.data_rows}
          />
        )}

        {/* Chart */}
        {message.chart_type &&
          message.chart_type !== 'none' &&
          message.data_columns &&
          message.data_rows &&
          message.data_rows.length > 1 && (
            <DataChart
              columns={message.data_columns}
              rows={message.data_rows}
              chartType={message.chart_type}
            />
          )}
      </div>
    </div>
  );
};
