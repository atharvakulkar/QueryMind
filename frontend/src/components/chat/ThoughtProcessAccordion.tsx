import { type FC, useState } from 'react';
import {
  ChevronDown,
  Code2,
  Database,
  GitBranch,
  Copy,
  Check,
  Lightbulb,
} from 'lucide-react';
import type { Message } from '@/types';
import { cn, highlightSQL } from '@/lib/utils';

interface ThoughtProcessAccordionProps {
  message: Message;
}

type AccordionSection = 'schema' | 'sql' | 'assumptions';

export const ThoughtProcessAccordion: FC<ThoughtProcessAccordionProps> = ({
  message,
}) => {
  const [openSections, setOpenSections] = useState<Set<AccordionSection>>(
    new Set(),
  );
  const [copiedSql, setCopiedSql] = useState(false);

  const toggle = (section: AccordionSection) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const handleCopySQL = async () => {
    if (!message.sql_query) return;
    try {
      await navigator.clipboard.writeText(message.sql_query);
      setCopiedSql(true);
      setTimeout(() => setCopiedSql(false), 2000);
    } catch {
      /* clipboard not available */
    }
  };

  const sections: {
    key: AccordionSection;
    label: string;
    icon: typeof Code2;
    content: React.ReactNode;
    show: boolean;
  }[] = [
    {
      key: 'schema',
      label: 'Schema Reflection',
      icon: Database,
      show: !!message.schema_link,
      content: message.schema_link && (
        <div className="space-y-3">
          {/* Tables */}
          <div>
            <p className="text-[10px] uppercase tracking-wider font-semibold text-[var(--color-text-tertiary)] mb-1.5">
              Tables Referenced
            </p>
            <div className="flex flex-wrap gap-1.5">
              {message.schema_link.tables.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-mono bg-[var(--color-brand-500)]/10 text-[var(--color-brand-300)] border border-[var(--color-brand-500)]/20"
                >
                  <Database className="w-3 h-3" />
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Columns */}
          {message.schema_link.columns.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider font-semibold text-[var(--color-text-tertiary)] mb-1.5">
                Columns Used
              </p>
              <div className="flex flex-wrap gap-1.5">
                {message.schema_link.columns.map((c) => (
                  <span
                    key={c}
                    className="px-2 py-1 rounded-md text-xs font-mono bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)]"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Join Hints */}
          {message.schema_link.join_hints.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider font-semibold text-[var(--color-text-tertiary)] mb-1.5">
                Join Hints
              </p>
              <div className="flex flex-wrap gap-1.5">
                {message.schema_link.join_hints.map((h, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs bg-[var(--color-bg-primary)] text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)]"
                  >
                    <GitBranch className="w-3 h-3 text-[var(--color-accent-400)]" />
                    {h}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'sql',
      label: 'Generated SQL',
      icon: Code2,
      show: !!message.sql_query,
      content: message.sql_query && (
        <div className="relative">
          <button
            onClick={handleCopySQL}
            className="absolute top-2 right-2 p-1.5 rounded-md hover:bg-[var(--color-bg-hover)] text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)] transition-colors duration-150"
            aria-label="Copy SQL"
          >
            {copiedSql ? (
              <Check className="w-3.5 h-3.5 text-[var(--color-success)]" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
          <pre className="code-block pr-10">
            <code>{highlightSQL(message.sql_query)}</code>
          </pre>
        </div>
      ),
    },
    {
      key: 'assumptions',
      label: 'Assumptions Made',
      icon: Lightbulb,
      show: !!message.assumptions && message.assumptions.length > 0,
      content: message.assumptions && (
        <ul className="space-y-1.5">
          {message.assumptions.map((a, i) => (
            <li
              key={i}
              className="flex items-start gap-2 text-xs text-[var(--color-text-secondary)]"
            >
              <span className="mt-1 w-1.5 h-1.5 rounded-full bg-[var(--color-accent-400)] shrink-0" />
              {a}
            </li>
          ))}
        </ul>
      ),
    },
  ];

  const visibleSections = sections.filter((s) => s.show);

  if (visibleSections.length === 0) return null;

  return (
    <div className="rounded-xl border border-[var(--color-border-subtle)] overflow-hidden divide-y divide-[var(--color-border-subtle)]">
      {visibleSections.map((section) => {
        const isOpen = openSections.has(section.key);
        const Icon = section.icon;

        return (
          <div key={section.key}>
            <button
              onClick={() => toggle(section.key)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-[var(--color-bg-hover)] transition-colors duration-150"
            >
              <div className="flex items-center gap-2">
                <Icon className="w-3.5 h-3.5 text-[var(--color-brand-400)]" />
                <span className="text-xs font-medium text-[var(--color-text-secondary)]">
                  {section.label}
                </span>
              </div>
              <ChevronDown
                className={cn(
                  'w-3.5 h-3.5 text-[var(--color-text-tertiary)] transition-transform duration-200',
                  isOpen && 'rotate-180',
                )}
              />
            </button>
            <div
              className={cn(
                'overflow-hidden transition-all duration-300 ease-in-out',
                isOpen ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0',
              )}
            >
              <div className="px-4 pb-4 pt-1">{section.content}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
